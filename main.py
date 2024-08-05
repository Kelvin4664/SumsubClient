import os
import hashlib
import hmac
import json
import logging
import time
import requests


class SumsubWrapper:
    def __init__(self, sumsub_secret:str, app_token:str, base_url:str) -> None:
        self.sumsub_secret = sumsub_secret
        self.app_token = app_token
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def _sign_request(self, method:str, path:str, body:dict) -> dict:
        """
        Signs the request following Sumsub's specification
        """
        timestamp = str(int(time.time()))
        message = f"{method.upper()}\n{path}\n{timestamp}\n{json.dumps(body)}"
        signature = hmac.new(
            self.sumsub_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return {
            "X-App-Token": self.app_token,
            "X-App-Access-Sig": signature,
            "X-App-Access-Ts": timestamp
        }
    
    def _request(self, method:str, path:str, body:dict=None, params:dict=None, *args, **kwargs) -> dict:

        headers = {
            'Content-Type': 'application/json',
            'Content-Encoding': 'utf-8'
            }
        path = f"{self.base_url}{path}"
        headers.update(self._sign_request(method, path, body))
        r = requests.Request(method, path, json=body, headers=headers, params=params, *args, **kwargs)
        prepared_request = r.prepare()
        session = requests.Session()
        response = session.send(prepared_request)
        response.raise_for_status()
        return response.json()
    
    # A: Implement logic to create an applicant
    # The method should return a `SumsubApplicant` object.
    def create_applicant(self, external_user_id:int, level_name:str) -> dict:
        path = f"/resources/applicants?levelName={level_name}"
        body = {"externalUserId": external_user_id}
        query_params = {"levelName": level_name}

        # Return the entire json object
        return self._request("POST", path, body, query_params)
    
    #B: Implement logic to add an ID document
    def add_id_document(self, applicant_id:str) -> dict:
        with open("some_document.jpg", "rb") as f:
            path = f"/resources/applicants/{applicant_id}/info/idDoc"
            body = {"metadata": '{"idDocType":"PASSPORT", "country":"USA"}'}
            files = {"content": f.read()} #Gets passed as a kwarg to the requests.post method
            response =  self._request("POST", path, body, files)
            doc_id = response.headers['X-Image-Id']
            # Do something with the doc_id?
            return doc_id
    
    #C. Get and Print Verification Status:
    def get_verification_status(self, applicant_id:str) -> dict:
        path = f"/resources/applicants/{applicant_id}/requiredIdDocsStatus"
        response = self._request("GET", path)
        review_status =  response.get("reviewStatus")
        print(f"Review Status: {review_status}")
        return review_status
    
    
    #D. Get and save verification data:
    def get_verification_data(self, applicant_id:str) -> dict:
        path = f"/resources/applicants/{applicant_id}/info"
        verification_data =  self._request("GET", path)
        # What i'd save from the above response is specific to the nature of application i am building
        # A safe bet would be to dump the entire response to a JSOB column if using postgres
        # or write it to a NoSQL database
        # No data store was specified in the requirements so i'd just write the response to a file
        # Solely for demonstration purpose, with the applicant ID as the filename
        with open(f"{applicant_id}.json", "w") as f:
            json.dump(verification_data, f)

        return verification_data
        

if __name__ == "__main__":
    SUMSUB_SECRET = os.environ.get("SUMSUB_SECRET")
    APP_TOKEN = os.environ.get("APP_TOKEN")
    BASE_URL = os.environ.get("BASE_URL")
    sumsub = SumsubWrapper(SUMSUB_SECRET, APP_TOKEN, BASE_URL)
    applicant_id = sumsub.create_applicant(123456, "basic-kyc-level")
    print(applicant_id)
    doc_id = sumsub.add_id_document(applicant_id)
    print(doc_id)
    verification_data = sumsub.get_verification_status(applicant_id)
    print(verification_data)
    verification_status = sumsub.get_verification_data(applicant_id)
    print(verification_status)

