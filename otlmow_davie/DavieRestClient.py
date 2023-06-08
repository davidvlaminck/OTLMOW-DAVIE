import logging
from pathlib import Path

from otlmow_davie.DavieDomain import AanleveringCreatie, AanleveringResultaat, Aanlevering, AanleveringBestandResultaat, \
    AsIsAanvraagResultaat, AsIsAanvraagCreatie, AsIsAanvraag
from otlmow_davie.JWTAsyncRequester import JWTAsyncRequester


class DavieRestClient:
    def __init__(self, requester: JWTAsyncRequester):
        self.requester = requester
        self.pagingcursor = ''

    async def get_aanlevering(self, id: str) -> Aanlevering:
        response = await self.requester.get(
            url=f'aanleveringen/{id}')
        response_text = await response.text()
        if response.status == 404:
            logging.debug(response)
            raise ValueError(f'Could not find aanlevering {id}.')
        elif response.status != 200:
            logging.debug(response)
            raise ProcessLookupError(response_text)

        return AanleveringResultaat.parse_raw(response_text).aanlevering

    async def create_aanlevering(self, nieuwe_aanlevering: AanleveringCreatie) -> Aanlevering:
        nieuwe_aanlevering = nieuwe_aanlevering.json()

        response = await self.requester.post(
            url=f'aanleveringen', data=nieuwe_aanlevering)
        response_text = await response.text()

        if str(response.status)[0] != '2': # TODO fix status code check
            print('Status:', response.status, 'Headers:', response.headers, 'Error Response:', response_text)
            raise RuntimeError('Could not create aanlevering.')

        resultaat = AanleveringResultaat.parse_raw(response_text)
        logging.debug(f"aanlevering succesvol aangemaakt, id is {resultaat.aanlevering.id}")
        return resultaat.aanlevering

    async def create_aanvraag_as_is(self, aanlevering_id: str, as_is_aanvraag_create: AsIsAanvraagCreatie) -> AsIsAanvraag:
        as_is_aanvraag_create_json = as_is_aanvraag_create.json()
        response = await self.requester.post(
            url=f'aanleveringen/{aanlevering_id}/asisaanvragen', data=as_is_aanvraag_create_json)
        response_text = await response.text()

        if response.status != 200:
            logging.debug(response)
            raise ValueError(f'Could not create as_aanvraag in aanlevering {aanlevering_id}.')

        resultaat = AsIsAanvraagResultaat.parse_raw(response_text)
        logging.debug(f"as_is_aanvraag succesvol aangemaakt, id is {resultaat.asisAanvraag.id}")
        return resultaat.asisAanvraag

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

    async def download_as_is_result(self, aanlevering_id, file_name: str, dir_path: Path, chunk_size:int = 1000) -> None:
        response = await self.requester.get(
            url=f'aanleveringen/{aanlevering_id}/asisaanvragen/export')
        if response.status != 200:
            logging.debug(response)
            raise ValueError(f'Could not download as is aanvraag in {aanlevering_id}.')

        with open(dir_path / file_name, 'wb') as f:
            async for chunk in response.content.iter_chunked(chunk_size):
                f.write(chunk)
