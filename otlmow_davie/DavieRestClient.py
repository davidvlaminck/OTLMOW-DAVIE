import logging
from pathlib import Path

from otlmow_davie.DavieDomain import AanleveringCreatie, AanleveringResultaat, Aanlevering, AanleveringBestandResultaat, \
    AsIsAanvraagResultaat, AsIsAanvraagCreatie, AsIsAanvraag, AanleveringHistoriekItem
from otlmow_davie.RequestHandler import RequestHandler


class DavieRestClient:
    def __init__(self, request_handler: RequestHandler, api_prefix: str = ''):
        self.request_handler = request_handler
        self.paging_cursor = ''
        self._apply_api_prefix(api_prefix)

    def _apply_api_prefix(self, api_prefix: str) -> None:
        normalized_prefix = api_prefix.strip('/')
        if not normalized_prefix:
            return

        prefix_with_trailing_slash = f'{normalized_prefix}/'
        current_base_url = self.request_handler.requester.first_part_url
        if not current_base_url.endswith('/'):
            current_base_url += '/'

        if current_base_url.endswith(prefix_with_trailing_slash):
            self.request_handler.requester.first_part_url = current_base_url
            return

        self.request_handler.requester.first_part_url = current_base_url + prefix_with_trailing_slash

    @staticmethod
    def _extract_data_items(payload, endpoint: str) -> list[dict]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get('data'), list):
            return payload['data']
        raise ValueError(f'Unexpected payload for {endpoint}: expected a list or an object with a data list.')

    def get_aanlevering(self, id: str) -> Aanlevering:
        response = self.request_handler.perform_get_request(
            url=f'aanleveringen/{id}')
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(f'Could not find aanlevering {id}.')
        elif response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        return AanleveringResultaat.model_validate_json(response.text).aanlevering

    def create_aanlevering(self, nieuwe_aanlevering: AanleveringCreatie) -> Aanlevering:
        nieuwe_aanlevering_json = nieuwe_aanlevering.model_dump_json()

        response = self.request_handler.perform_post_request(
            url='aanleveringen', data=nieuwe_aanlevering_json)
        if response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        resultaat = AanleveringResultaat.model_validate_json(response.text)
        logging.debug(f"aanlevering succesvol aangemaakt, id is {resultaat.aanlevering.id}")
        return resultaat.aanlevering

    def create_aanvraag_as_is(self, aanlevering_id: str, as_is_aanvraag_create: AsIsAanvraagCreatie) -> AsIsAanvraag:
        as_is_aanvraag_create_json = as_is_aanvraag_create.model_dump_json()
        response = self.request_handler.perform_post_request(
            url=f'aanleveringen/{aanlevering_id}/asisaanvragen', data=as_is_aanvraag_create_json)

        if response.status_code != 200:
            logging.debug(response)
            raise ValueError(f'Could not create as_aanvraag in aanlevering {aanlevering_id}.')

        resultaat = AsIsAanvraagResultaat.model_validate_json(response.text)
        logging.debug(f"as_is_aanvraag succesvol aangemaakt, id is {resultaat.asisAanvraag.id}")
        return resultaat.asisAanvraag

    def get_historiek(self, id: str) -> list[AanleveringHistoriekItem]:
        response = self.request_handler.perform_get_request(
            url=f'aanleveringen/{id}/historiek')
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(f'Could not find aanlevering {id}.')
        elif response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        historiek_items = self._extract_data_items(response.json(), endpoint='historiek')
        return [AanleveringHistoriekItem.model_validate(item) for item in historiek_items]

    def list_files(self, id: str) -> list[AanleveringBestandResultaat]:
        response = self.request_handler.perform_get_request(
            url=f'aanleveringen/{id}/bestanden')
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(f'Could not find aanlevering {id}.')
        elif response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        file_items = self._extract_data_items(response.json(), endpoint='bestanden')
        return [AanleveringBestandResultaat.model_validate(item) for item in file_items]

    def upload_file(self, id: str, file_path: Path) -> AanleveringBestandResultaat:
        with open(file_path, "rb") as data:
            response = self.request_handler.perform_post_request(
                url=f'aanleveringen/{id}/bestanden/binary',
                params={"bestandsnaam": file_path.name},
                data=data)
            if response.status_code == 404:
                logging.debug(response)
                raise ValueError(f'Could not find aanlevering {id}.')
            elif response.status_code != 200:
                logging.debug(response)
                raise ProcessLookupError(response.content.decode("utf-8"))
            resultaat = AanleveringBestandResultaat.model_validate_json(response.text)
            print(resultaat.model_dump_json())
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

    def download_as_is_result(self, aanlevering_id, file_name: str, dir_path: Path) -> None:
        response = self.request_handler.perform_get_request(
            url=f'aanleveringen/{aanlevering_id}/asisaanvragen/export')
        if response.status_code != 200:
            logging.debug(response)
            raise ValueError(f'Could not download as is aanvraag in {aanlevering_id}.')

        with open(dir_path / file_name, 'wb') as f:
            f.write(response.content)
