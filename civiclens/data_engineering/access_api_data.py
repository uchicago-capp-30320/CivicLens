import time
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter

"""
This code pulls heavily from the following existing repositories:

https://github.com/willjobs/regulations-public-comments
https://github.com/jacobfeldgoise/regulations-comments-downloader
"""


def _is_duplicated_on_server(response_json):
    """Used to determine whether a given response indicates a duplicate on the server. This is
    because there is a bug in the server: there are some commentIds, like NRCS-2009-0004-0003,
    which correspond to multiple actual comments! This function determines whether the
    returned JSON has an error indicating this issue

    Args:
        response_json (dict): JSON from request to API (usually, from get_request_json)

    Returns:
        bool: whether the response indicates a duplicate issue or not
    """
    return (
        ("errors" in response_json.keys())
        and (response_json["errors"][0]["status"] == "500")
        and (response_json["errors"][0]["detail"][:21] == "Incorrect result size")
    )


def api_date_format_params(data_type, start_date=None, end_date=None):
    """
    Formats dates to be passed to API call. Assumes we want whole days, and
    aren't filtering by time.

    Inputs:
        data_type (str): 'dockets', 'documents', or 'comments' -- what kind of data we want back from the API
        start_date (str in YYYY-MM-DD format, optional): the inclusive start date of our data pull
        end_date (str in YYYY-MM-DD format, optional): the inclusive end date of our data pull

    Returns:
        date_param (dict): dict containing the right formatted date calls
    """
    date_param = {}
    if data_type == "dockets":
        if start_date:
            date_param.update(
                {"filter[lastModifiedDate][ge]": f"{start_date} 00:00:00"}
            )
        if end_date:
            date_param.update({"filter[lastModifiedDate][le]": f"{end_date} 23:59:59"})
    else:
        if start_date:
            date_param.update({"filter[postedDate][ge]": start_date})
        if end_date:
            date_param.update({"filter[postedDate][le]": end_date})

    return date_param


def pull_reg_gov_data(
    api_key,
    data_type,
    start_date=None,
    end_date=None,
    params=None,
    print_remaining_requests=False,
    skip_duplicates=False,
):
    """
    Returns the JSON associated with a request to the API; max length of 24000

    draws heavily from here: https://github.com/willjobs/regulations-public-comments/blob/master/comments_downloader.py

    Args:
        data_type (str): 'dockets', 'documents', or 'comments' -- what kind of data we want back from the API
        start_date (str in YYYY-MM-DD format, optional): the inclusive start date of our data pull
        end_date (str in YYYY-MM-DD format, optional): the inclusive end date of our data pull
        params (dict, optional): Parameters to specify to the endpoint request. Defaults to None.
            If we are querying the non-details endpoint, we also append the "page[size]" parameter
            so that we always get the maximum page size of 250 elements per page.
        print_remaining_requests (bool, optional): Whether to print out the number of remaining
            requests this hour, based on the response headers. Defaults to False.
        skip_duplicates (bool, optional): If a request returns multiple items when only 1 was expected,
            should we skip that request? Defaults to False.

    Returns:
        dict: JSON-ified request response
    """
    # generate the right API request
    api_url = "https://api.regulations.gov/v4/"
    endpoint = f"{api_url}{data_type}"
    params = params if params is not None else {}

    # Our API key has a rate limit of 1,000 requests/hour. If we hit that limit, we can
    # retry every WAIT_MINUTES minutes (more frequently than once an hour, in case our request limit
    # is updated sooner). We will sleep for POLL_SECONDS seconds at a time to see if we've been
    # interrupted. Otherwise we'd have to wait a while before getting interrupted. We could do this
    # with threads, but that gets more complicated than it needs to be.
    STATUS_CODE_OVER_RATE_LIMIT = 429
    WAIT_SECONDS = 3600  # Default to 1 hour

    # if any dates are specified, format those and add to the params
    if start_date or end_date:
        param_dates = api_date_format_params(data_type, start_date, end_date)
        params.update(param_dates)

    # whether we are querying the search endpoint (e.g., /documents) or the "details" endpoint
    if endpoint.split("/")[-1] in ["dockets", "documents", "comments"]:
        params = {**params, "page[size]": 250}  # always get max page size

    # Rather than do requests.get(), use this approach to (attempt to) gracefully handle noisy connections to the server
    # We sometimes get SSL errors (unexpected EOF or ECONNRESET), so this should hopefully help us retry.
    session = requests.Session()
    session.mount("https", HTTPAdapter(max_retries=4))

    def poll_for_response(api_key, wait_for_rate_reset):
        r = session.get(
            endpoint, headers={"X-Api-Key": api_key}, params=params, verify=True
        )

        if r.status_code == 200:
            # SUCCESS! Return the JSON of the request
            num_requests_left = int(r.headers["X-RateLimit-Remaining"])
            if (
                print_remaining_requests
                or (num_requests_left < 10)
                or (num_requests_left <= 100 and num_requests_left % 10 == 0)
                or (num_requests_left % 100 == 0 and num_requests_left < 1000)
            ):
                print(f"(Requests left: {r.headers['X-RateLimit-Remaining']})")

            return [True, r.json()]
        else:
            if r.status_code == STATUS_CODE_OVER_RATE_LIMIT and wait_for_rate_reset:
                the_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                retry_after = r.headers.get("Retry-After", None)
                wait_time = (
                    int(retry_after)
                    if retry_after and retry_after.isdigit()
                    else WAIT_SECONDS
                )
                print(
                    f"Rate limit exceeded at {the_time}. Waiting {wait_time} seconds to retry."
                )
                time.sleep(wait_time)
            elif _is_duplicated_on_server(r.json()) and skip_duplicates:
                print("****Duplicate entries on server. Skipping.")
                print(r.json()["errors"][0]["detail"])
            else:  # some other kind of error
                print([r, r.status_code])
                print(r.json())
                r.raise_for_status()

        return [False, r.json()]

    doc_data = None  # Initialize doc_data to None
    for i in range(1, 21):  # Fetch up to 20 pages
        params["page[number]"] = str(i)  # Add page number to the params

        success, r_json = poll_for_response(api_key, wait_for_rate_reset=True)

        if success or (_is_duplicated_on_server(r_json) and skip_duplicates):
            if doc_data is not None:
                doc_data += r_json["data"]
            else:
                doc_data = r_json["data"]

            # Break if it's the last page
            if r_json["meta"]["lastPage"]:
                return doc_data

    raise RuntimeError(f"Unrecoverable error; {r_json}")


def get_comment_text(api_key: str, comment_id: str) -> dict:
    """
    Get the text of a comment

    Args:
        api_key (str): key for the regulations.gov API
        comment_id (str): the id for the comment

    Returns: 
        JSON object for the comment text
    """
    api_url = "https://api.regulations.gov/v4/comments/"
    endpoint = f"{api_url}{comment_id}?include=attachments&api_key={api_key}"
    response = requests.get(endpoint)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


def merge_comment_text_and_data(api_key: str, comment_data: dict) -> dict:
    """
    Combine comment json object with the comment text json object

    Args:
        api_key (str): key for the regulations.gov API
        comment_data (json): the json object from regulations.gov

    Returns:
        Combined json object for the comment and text
    """

    comment_text_data = get_comment_text(api_key, comment_data["id"])

    # DECISION: only track the comment data; don't include the info on comment
    # attachments which is found elsewhere in comment_text_data

    all_comment_data = {**comment_data, **comment_text_data}
    return all_comment_data


