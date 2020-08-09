from typing import Optional, Dict, Union, Any
from requests import Response
import requests
import time
from authlib.jose import jwt
import syslog


class ZoomHelper:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.zoom.us/v2"
        self.reports_url = f"{self.base_url}/report/meetings"
        self.jwt_token_exp = 1800
        self.jwt_token_algo = "HS256"

    def get_meeting_participants(self,
                                 meeting_id: str,
                                 jwt_token: bytes,
                                 next_page_token: Optional[str] = None) -> Response:
        url = f"{self.reports_url}/{meeting_id}/participants"
        query_params: Dict[str, Union[int, str]] = {"page_size": 300}
        if next_page_token:
            query_params.update({"next_page_token": next_page_token})
        syslog.syslog(f"Getting participants for {meeting_id}")
        r: Response = requests.get(url,
                                   headers={"Authorization": f"Bearer {jwt_token.decode('utf-8')}"},
                                   params=query_params)
        return r

    def generate_jwt_token(self) -> bytes:
        iat = int(time.time())

        jwt_payload: Dict[str, Any] = {
            "aud": None,
            "iss": self.api_key,
            "exp": iat + self.jwt_token_exp,
            "iat": iat
        }

        header: Dict[str, str] = {"alg": self.jwt_token_algo}

        jwt_token: bytes = jwt.encode(header, jwt_payload, self.api_secret)

        return jwt_token

    def get_meeting_details(self,
                            meeting_id: str,
                            jwt_token: bytes) -> Response:
        url = f"{self.reports_url}/meetings/{meeting_id}"

        syslog.syslog(f"Getting meeting details for {meeting_id}")
        r: Response = requests.get(url,
                                   headers={"Authorization": f"Bearer {jwt_token.decode('utf-8')}"})
        return r
