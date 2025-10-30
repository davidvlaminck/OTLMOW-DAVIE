import json
import logging
from pathlib import Path

from otlmow_davie.DavieDomain import AanleveringCreatie, AanleveringResultaat, Aanlevering, AanleveringBestandResultaat, \
    AsIsAanvraagResultaat, AsIsAanvraagCreatie, AsIsAanvraag, OpgelijsteAanlevering, PagedOpgelijsteAanleveringResultaat
from otlmow_davie.Enums import AuthType, Environment
from otlmow_davie.RequestHandler import RequestHandler
from otlmow_davie.RequesterFactory import RequesterFactory


class DavieInternalRestClient:
    def __init__(self, auth_type: AuthType, env: Environment, settings_path: Path = None, cookie: str = None,
                 use_services: bool = True):
        self.requester = RequesterFactory.create_requester(auth_type=auth_type, env=env, settings_path=settings_path,
                                                           cookie=cookie, use_services=use_services)
        self.requester.first_part_url += 'davie-aanlevering/api/'
        self.pagingcursor = ''

    def zoek_aanleveringen(self, from_: int = 0, size: int = 100, search_dict: dict = {}) -> OpgelijsteAanlevering:
        if 'sortBy' not in search_dict:
            search_dict['sortBy'] = {
                "property": "creatieDatum",
                "order": "desc"
            }

        response = self.requester.post(
            url=f'aanleveringen/zoek?from={from_}&size={size}', data=json.dumps(search_dict))
        if response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))

        opgelijste_resultaat = PagedOpgelijsteAanleveringResultaat.model_validate(json.loads(response.text))
        total = opgelijste_resultaat.total

        yielded_total = 0
        while yielded_total < total:
            for resultaat in opgelijste_resultaat.data:
                yield resultaat.aanlevering
                yielded_total += 1
            if yielded_total == total:
                break
            from_ += size
            response = self.requester.post(
                url=f'aanleveringen/zoek?from={from_}&size={size}', data=json.dumps(search_dict))
            if response.status_code != 200:
                logging.debug(response)
                raise ProcessLookupError(response.content.decode("utf-8"))
            opgelijste_resultaat = PagedOpgelijsteAanleveringResultaat.model_validate(json.loads(response.text))

