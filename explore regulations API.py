import requests
import json
import datetime
from requests.adapters import HTTPAdapter

import pandas as pd
import matplotlib as plt


def get_document_ids(docket_id, api_key):
    docs_url = "https://api.regulations.gov/v4/documents?filter[docketId]={}&api_key={}".format(
        docket_id, api_key
    )
    data = json.loads(requests.get(docs_url).text)

    if ("error" in data) and (data["error"]["code"] == "OVER_RATE_LIMIT"):
        print(
            "["
            + str(datetime.datetime.now())
            + "] "
            + "You've exceeded your API limit! Wait an hour and try again. Don't worry, we saved your progress."
        )
        return None

    data = data["data"]
    doc_ids = []
    doc_links = []
    for i in range(len(data)):
        doc_ids.append(data[i]["attributes"]["objectId"])
        doc_links.append(data[i]["links"]["self"])

    print(
        "["
        + str(datetime.datetime.now())
        + "] "
        + "Retrieved {} documents for docket {}".format(len(doc_ids), docket_id)
    )
    return doc_ids, doc_links


def get_request_json(
    self,
    endpoint,
    params=None,
    print_remaining_requests=False,
    wait_for_rate_limits=False,
    skip_duplicates=False,
):
    """Used to return the JSON associated with a request to the API

    Args:
        endpoint (str): URL of the API to access (e.g., https://api.regulations.gov/v4/documents)
        params (dict, optional): Parameters to specify to the endpoint request. Defaults to None.
            If we are querying the non-details endpoint, we also append the "page[size]" parameter
            so that we always get the maximum page size of 250 elements per page.
        print_remaining_requests (bool, optional): Whether to print out the number of remaining
            requests this hour, based on the response headers. Defaults to False.
        wait_for_rate_limits (bool, optional): Determines whether to wait to re-try if we run out of
            requests in a given hour. Defaults to False.
        skip_duplicates (bool, optional): If a request returns multiple items when only 1 was expected,
            should we skip that request? Defaults to False.

    Returns:
        dict: JSON-ified request response
    """

    # Our API key has a rate limit of 1,000 requests/hour. If we hit that limit, we can
    # retry every WAIT_MINUTES minutes (more frequently than once an hour, in case our request limit
    # is updated sooner). We will sleep for POLL_SECONDS seconds at a time to see if we've been
    # interrupted. Otherwise we'd have to wait a while before getting interrupted. We could do this
    # with threads, but that gets more complicated than it needs to be.
    STATUS_CODE_OVER_RATE_LIMIT = 429
    WAIT_MINUTES = 20  # time between attempts to get a response
    POLL_SECONDS = (
        10  # run time.sleep() for this long, so we can check if we've been interrupted
    )

    params = params if params is not None else {}

    # whether we are querying the search endpoint (e.g., /documents) or the "details" endpoint
    if endpoint.split("/")[-1] in ["dockets", "documents", "comments"]:
        params = {**params, "page[size]": 250}  # always get max page size

    # Rather than do requests.get(), use this approach to (attempt to) gracefully handle noisy connections to the server
    # We sometimes get SSL errors (unexpected EOF or ECONNRESET), so this should hopefully help us retry.
    session = requests.Session()
    session.mount("https", HTTPAdapter(max_retries=4))

    def poll_for_response(api_key, else_func):
        r = session.get(
            endpoint, headers={"X-Api-Key": api_key}, params=params, verify=False
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
            if r.status_code == STATUS_CODE_OVER_RATE_LIMIT and wait_for_rate_limits:
                else_func()
            elif self._is_duplicated_on_server(r.json()) and skip_duplicates:
                print("****Duplicate entries on server. Skipping.")
                print(r.json()["errors"][0]["detail"])
            else:  # some other kind of error
                print([r, r.status_code])
                print(r.json())
                r.raise_for_status()

        return [False, r.json()]

    def wait_for_requests():
        the_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{the_time}: Hit rate limits. Waiting {WAIT_MINUTES} minutes to try again",
            flush=True,
        )
        # We ran out of requests. Wait for WAIT_MINUTES minutes, but poll every POLL_SECONDS seconds for interruptions
        for i in range(int(WAIT_MINUTES * 60 / POLL_SECONDS)):
            time.sleep(POLL_SECONDS)

    for _ in range(1, int(60 / WAIT_MINUTES) + 3):
        success, r_json = poll_for_response(self.api_key, wait_for_requests)

        if success or (self._is_duplicated_on_server(r_json) and skip_duplicates):
            return r_json

    print(r_json)
    raise RuntimeError(f"Unrecoverable error; {r_json}")


def get_items_count(self, data_type, params):
    """Gets the number of items returned by a request in the totalElements attribute.

    Args:
        data_type (str): One of "dockets", "documents", or "comments".
        params (dict): Parameters to specify to the endpoint request for the query. See details
            on available parameters at https://open.gsa.gov/api/regulationsgov/.

    Returns:
        int: Number of items returned by request
    """
    # make sure the data_type is plural
    data_type = data_type if data_type[-1:] == "s" else data_type + "s"

    r_items = self.get_request_json(
        f"https://api.regulations.gov/v4/{data_type}", params=params
    )
    totalElements = r_items["meta"]["totalElements"]
    return totalElements
