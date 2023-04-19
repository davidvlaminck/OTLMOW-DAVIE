import logging
from pathlib import Path

from otlmow_davie.DavieDomain import AanleveringCreatie, AanleveringResultaat, Aanlevering, AanleveringBestandResultaat
from otlmow_davie.RequestHandler import RequestHandler


class DavieRestClient:
    def __init__(self, request_handler: RequestHandler):
        self.request_handler = request_handler
        self.pagingcursor = ''

    def get_aanlevering(self, id: str) -> Aanlevering:
        response = self.request_handler.perform_get_request(
            url=f'aanleveringen/{id}')
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(f'Could not find aanlevering {id}.')
        elif response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        return AanleveringResultaat.parse_raw(response.text).aanlevering

    def create_aanlevering(self, nieuwe_aanlevering: AanleveringCreatie) -> Aanlevering:
        nieuwe_aanlevering = nieuwe_aanlevering.json()

        response = self.request_handler.perform_post_request(
            url=f'aanleveringen', data=nieuwe_aanlevering)
        if response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        resultaat = AanleveringResultaat.parse_raw(response.text)
        logging.debug(f"aanlevering succesvol aangemaakt, id is {resultaat.aanlevering.id}")
        return resultaat.aanlevering

    def upload_file(self, id: str, file_path: Path) -> AanleveringBestandResultaat:
        with open(file_path, "rb") as data:
            response = self.request_handler.perform_post_request(
                url=f'aanleveringen/{id}/bestanden',
                params={"bestandsnaam": file_path.name},
                data=data)
            if response.status_code == 404:
                logging.debug(response)
                raise ValueError(f'Could not find aanlevering {id}.')
            elif response.status_code != 200:
                logging.debug(response)
                raise ProcessLookupError(response.content.decode("utf-8"))
            resultaat = AanleveringBestandResultaat.parse_raw(response.text)
            print(resultaat.json())
            logging.debug(f"Uploaded file {file_path} to aanlevering {id}")
            return resultaat

    def finalize(self, id: str) -> None:
        response = self.request_handler.perform_post_request(
            url=f'aanleveringen/{id}/bestanden/finaliseer')
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(f'Could not find aanlevering {id}.')
        elif response.status_code != 204:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        logging.debug('finalize succeeded')


