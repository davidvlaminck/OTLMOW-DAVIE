import json

from otlmow_davie.RequestHandler import RequestHandler


class DavieRestClient:
    def __init__(self, request_handler: RequestHandler):
        self.request_handler = request_handler
        self.request_handler.requester.first_part_url += 'davie-core/public-api/'
        self.pagingcursor = ''

    def get_aanlevering(self, aanlevering_uuid: str):
        response = self.request_handler.perform_post_request(
            url=f'aanleveringen/{aanlevering_uuid}')
        if response.status_code != 200:
            print(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
