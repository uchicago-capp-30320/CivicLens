import requests
import time
import datetime
import pandas as pd

class BulkDl:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.regulations.gov/v4"
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        self.api_call_count = 0
        self.agencies = [
            "AID", "ATBCB", "CFPB", "CNCS", "COLC", "CPPBSD", "CPSC", "CSB", "DHS",
            "DOC", "DOD", "DOE", "DOI", "DOJ", "DOL", "DOS", "DOT", "ED", "EEOC",
            "EIB", "EOP", "EPA", "FFIEC", "FMC", "FRTIB", "FTC", "GAPFAC", "GSA",
            "HHS", "HUD", "NARA", "NASA", "NCUA", "NLRB", "NRC", "NSF", "NTSB",
            "ONCD", "OPM", "PBGC", "PCLOB", "SBA", "SSA", "TREAS", "USC", "USDA", "VA",
            "ACF", "ACL", "AHRQ", "AID", "AMS", "AOA", "APHIS", "ARS", "ASC", "ATBCB",
            "ATF", "ATR", "ATSDR", "BIA", "BIS", "BLM", "BLS", "BOEM", "BOP", "BOR",
            "BPA", "BPD", "BSC", "BSEE", "CCC", "CDC", "CDFI", "CEQ", "CFPB", "CISA",
            "CMS", "CNCS", "COE", "COLC", "CPPBSD", "CPSC", "CSB", "CSEO", "CSREES", "DARS",
            "DEA", "DEPO", "DHS", "DOC", "DOD", "DOE", "DOI", "DOJ", "DOL", "DOS", "DOT",
            "EAB", "EAC", "EBSA", "ECAB", "ECSA", "ED", "EDA", "EEOC", "EERE", "EIA", "EIB",
            "EOA", "EOIR", "EPA", "ERS", "ESA", "ETA", "FAA", "FAR", "FAS", "FBI", "FCIC",
            "FCSC", "FDA", "FEMA", "FFIEC", "FHWA", "FINCEN", "FIRSTNET", "FISCAL", "FLETC",
            "FMC", "FMCSA", "FNS", "FPAC", "FRA", "FRTIB", "FS", "FSA", "FSIS", "FSOC",
            "FTA", "FTC", "FTZB", "FWS", "GAPFAC", "GIPSA", "GSA", "HHS", "HHSIG", "HRSA",
            "HUD", "IACB", "ICEB", "IHS", "IPEC", "IRS", "ISOO", "ITA", "LMSO", "MARAD",
            "MBDA", "MMS", "MSHA", "NAL", "NARA", "NASA", "NASS", "NCS", "NCUA", "NEO",
            "NHTSA", "NIC", "NIFA", "NIGC", "NIH", "NIST", "NLRB", "NNSA", "NOAA", "NPS",
            "NRC", "NRCS", "NSF", "NSPC", "NTIA", "NTSB", "OCC", "OEPNU", "OFAC", "OFCCP",
            "OFPP", "OFR", "OJJDP", "OJP", "OMB", "ONCD", "ONDCP", "ONRR", "OPM", "OPPM",
            "OSHA", "OSM", "OSTP", "OTS", "PBGC", "PCLOB", "PHMSA", "PTO", "RBS", "RHS",
            "RITA", "RMA", "RTB", "RUS", "SAMHSA", "SBA", "SEPA", "SLSDC", "SSA", "SWPA",
            "TA", "TREAS", "TSA", "TTB", "USA", "USAF", "USBC", "USCBP", "USCG", "USCIS",
            "USDA", "USDAIG", "USGS", "USMINT", "USN", "USPC", "USTR", "VA", "VETS", "WAPA",
             "WCPO", "WHD"
        ]
    
    def fetch_all_pages(self, endpoint, params, max_items_per_page=250):
        '''
        Helper function to fetch max pages(250 x 20) for a given endpoint
        '''
        items = []
        page = 1
        while True:
            params['page[number]'] = page
            params['page[size]'] = max_items_per_page

            response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
            print(f"Requesting: {response.url}")

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    print("Failed to decode JSON response")
                    break
                items.extend(data['data'])
                if not data['meta'].get('hasNextPage', False):
                    break
                page += 1
            elif response.status_code == 429:  # Rate limit exceeded, obtain reset time
                retry_after = response.headers.get("Retry-After", None)
                wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 3600  # Default to 1 hour if no wait time provided
                # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Rate limit exceeded. Waiting to {wait_time} seconds to retry.")
                time.sleep(wait_time)
                continue
            else:
                print(f"Error fetching page {page}: {response.status_code}")
                break
        return items


    def get_all_dockets_by_agency(self):
        '''
        Helper function to retrieve all docket ids. loops through 47 agencies as described in
        https://www.regulations.gov/agencies
        
        Note: This function represents the method to retrieve the entire list of docket ids. 
        '''
        all_docket_ids = set()

        for agency in self.agencies:
            filter_params = {'filter[agencyId]': agency}

            agency_dockets = self.fetch_all_pages('dockets', filter_params)

            all_docket_ids.update(docket['id'] for docket in agency_dockets)

            # Store as pandas dataframe.
            # We can change this mode of storage if you have a different idea, 
            # I think this is a sensible approach, to limit use of our API calls. 
            df = pd.DataFrame(all_docket_ids).drop_duplicates()
            df.to_csv('dockets.csv', index=False)

    def fetch_documents_by_date_ranges(self, start_date, end_date):
        '''
        Fetches documents posted within the given date ranges and saves them to a CSV file.
        '''
        all_documents = []
        for start, end in self.generate_date_ranges(start_date, end_date):
            print(f"Fetching documents from {start} to {end}")
            params = {
                'filter[postedDate][ge]': start.strftime("%Y-%m-%d"),
                'filter[postedDate][le]': end.strftime("%Y-%m-%d")
            }
            documents = self.fetch_all_pages('documents', params)
            all_documents.extend(documents)

        print(f"Total documents fetched: {len(all_documents)}")

        # Extract document IDs, openForComment
        document_lst = [(doc['id'], doc['attributes']['openForComment']) for doc in all_documents]

        # Save to DataFrame and CSV
        df = pd.DataFrame(document_lst, columns=['Doc_ID', 'openForComment'])
        print(f"Unique documents before deduplication: {len(df)}")
        df = df.drop_duplicates()
        print(f"Unique documents after deduplication: {len(df)}")
        df.to_csv('doc_ids_2014.csv', index=False)
        print("Document IDs have been saved to 'doc_ids.csv'.")

    @staticmethod # for now, we can put this in utils if that is preferred.
    def generate_date_ranges(start_date, end_date):
        '''
        Helper function to dynamically return weekly date-ranges. 

        Used in fetch_documents_by_date_ranges() to generate week blocks 
        to download documents
        '''
        current_date = start_date
        while current_date < end_date:
            week_end = current_date + datetime.timedelta(days=6)
            yield (current_date, min(week_end, end_date))
            current_date = week_end + datetime.timedelta(days=1)

    