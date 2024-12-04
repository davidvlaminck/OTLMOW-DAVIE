import logging
from pathlib import Path

from otlmow_davie.DavieDomain import AanleveringCreatie, AanleveringResultaat, Aanlevering, AanleveringBestandResultaat, \
    AsIsAanvraagResultaat, AsIsAanvraagCreatie, AsIsAanvraag, OpgelijsteAanlevering, PagedOpgelijsteAanleveringResultaat
from otlmow_davie.RequestHandler import RequestHandler


class DavieInternalRestClient:
    def __init__(self, request_handler: RequestHandler):
        self.request_handler = request_handler
        self.request_handler.requester.first_part_url += 'davie-aanlevering/api/'
        self.pagingcursor = ''

    def zoek_aanleveringen(self, from_: int = 0, size: int = 100) -> OpgelijsteAanlevering:
        d = {
            "sortBy": {
                "property": "creatieDatum",
                "order": "desc"
            }
        }
        response = self.request_handler.perform_post_request(
            url=f'aanleveringen/zoek?from={from_}&size={size}', data=d)
        if response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))

        opgelijste_resultaat = PagedOpgelijsteAanleveringResultaat.parse_raw(response.text)
        total = opgelijste_resultaat.total

        yielded_total = 0
        while yielded_total < total:
            for resultaat in opgelijste_resultaat.data:
                yield resultaat.aanlevering
                yielded_total += 1
            if yielded_total == total:
                break
            from_ += size
            response = self.request_handler.perform_post_request(
                url=f'aanleveringen/zoek?from={from_}&size={size}')
            if response.status_code != 200:
                logging.debug(response)
                raise ProcessLookupError(response.content.decode("utf-8"))
            opgelijste_resultaat = PagedOpgelijsteAanleveringResultaat.parse_raw(response.text)
