import json
from typing import Union

from requests import Response

from otlmow_davie.CertRequester import CertRequester
from otlmow_davie.JWTRequester import JWTRequester


class RequestHandler:
    def __init__(self, requester: Union[CertRequester, JWTRequester]):
        self.requester = requester

    def get_jsondict(self, url):
        response = self.perform_get_request(url)
        decoded_string = response.content.decode("utf-8")
        dict_obj = json.loads(decoded_string)
        return dict_obj

    def perform_get_request(self, url: str) -> Response:
        return self.requester.get(url=url)

    def perform_post_request(self, url: str, json_data=None, **kwargs) -> Response:
        if json_data is not None:
            kwargs['json'] = json_data
        return self.requester.post(url=url, **kwargs)

    def perform_put_request(self, url: str, json_data=None, **kwargs) -> Response:
        if json_data is not None:
            kwargs['json'] = json_data
        return self.requester.put(url=url, **kwargs)

    def perform_patch_request(self, url: str, json_data=None, **kwargs) -> Response:
        if json_data is not None:
            kwargs['json'] = json_data
        return self.requester.patch(url=url, **kwargs)

    def perform_delete_request(self, url: str, json_data=None, **kwargs) -> Response:
        if json_data is not None:
            kwargs['json'] = json_data
        return self.requester.delete(url=url, **kwargs)
