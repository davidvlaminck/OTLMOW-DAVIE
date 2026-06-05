import logging
from pathlib import Path
from typing import Optional

from otlmow_davie.DavieDomain import AanleveringCreatie, AanleveringResultaat, Aanlevering, AanleveringBestandResultaat, \
    AsIsAanvraagResultaat, AsIsAanvraagCreatie, AsIsAanvraag, LosseValidatieResultaat, LosseValidatie, \
    LosseValidatieBestandResultaat, PagedLosseValidatieBestandResultaat
from otlmow_davie.RequestHandler import RequestHandler


class DavieRestClient:
    def __init__(self, request_handler: RequestHandler, api_prefix: str = ''):
        """Implementeert van https://apps.mow.vlaanderen.be/applicatiedocumentatie/davie-core/b2b/swagger/index.html"""
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
    def _parse_paged_or_list(payload, paged_model, item_model, endpoint: str):
        if isinstance(payload, dict):
            return paged_model.model_validate(payload).data
        if isinstance(payload, list):
            return [item_model.model_validate(item) for item in payload]
        raise ValueError(f'Unexpected payload for {endpoint}: expected a list or an object with a data list.')

    @staticmethod
    def _perform_get_json_request(request_handler: RequestHandler, url: str, not_found_message: str, **kwargs):
        response = request_handler.perform_get_request(url=url, **kwargs)
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(not_found_message)
        if response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        return response.json()

    @staticmethod
    def _perform_get_binary_request(request_handler: RequestHandler, url: str, not_found_message: str, failure_message: str):
        response = request_handler.perform_get_request(url=url)
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(not_found_message)
        if response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(failure_message + '\n' + response.content.decode("utf-8"))
        return response.content

    @staticmethod
    def _download_to_file(request_handler: RequestHandler, url: str, not_found_message: str,
                          failure_message: str, file_name: str, dir_path: Path) -> None:
        content = DavieRestClient._perform_get_binary_request(
            request_handler=request_handler,
            url=url,
            not_found_message=not_found_message,
            failure_message=failure_message,
        )
        with open(dir_path / file_name, 'wb') as f:
            f.write(content)

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

    def get_losse_validatie(self, id: str) -> LosseValidatie:
        response = self.request_handler.perform_get_request(url=f'lossevalidaties/{id}')
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(f'Could not find lossevalidatie {id}.')
        if response.status_code != 200:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        return LosseValidatieResultaat.model_validate_json(response.text).losseValidatie

    def list_losse_validatie_bestanden(self, id: str, from_: int = 0, size: int = 100) -> list[LosseValidatieBestandResultaat]:
        bestand_payload = self._perform_get_json_request(
            self.request_handler, url=f'lossevalidaties/{id}/bestanden',
            not_found_message=f'Could not find lossevalidatie {id}.', params={'from': from_, 'size': size})
        return self._parse_paged_or_list(
            payload=bestand_payload,
            paged_model=PagedLosseValidatieBestandResultaat,
            item_model=LosseValidatieBestandResultaat,
            endpoint='lossevalidatie bestanden',
        )

    def upload_file(self, id: str, file_path: Path) -> Optional[AanleveringBestandResultaat]:
        with open(file_path, "rb") as data:
            response = self.request_handler.perform_post_request(
                url=f'aanleveringen/{id}/bestanden',
                params={"bestandsnaam": file_path.name},
                data=data)
            if response.status_code == 404:
                logging.debug(response)
                raise ValueError(f'Could not find aanlevering {id}.')
            elif response.status_code == 204:
                logging.debug(f'File chunk accepted for aanlevering {id}, waiting for remaining chunks.')
                return None
            elif response.status_code != 200:
                logging.debug(response)
                raise ProcessLookupError(response.content.decode("utf-8"))
            resultaat = AanleveringBestandResultaat.model_validate_json(response.text)
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

    def delete_file(self, aanlevering_id: str, bestand_id: str) -> None:
        response = self.request_handler.perform_delete_request(
            url=f'aanleveringen/{aanlevering_id}/bestanden/{bestand_id}')
        if response.status_code == 404:
            logging.debug(response)
            raise ValueError(f'Could not find aanlevering {aanlevering_id} or bestand {bestand_id}.')
        if response.status_code != 204:
            logging.debug(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        logging.debug(f'delete bestand succeeded for aanlevering {aanlevering_id}, bestand {bestand_id}')

    def download_as_is_result(self, aanlevering_id, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/asisaanvragen/export',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download as is aanvraag in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_as_is_errors(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/asisaanvragen/fouten',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download as is errors in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_doorstromingfouten(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/doorstromingfouten',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download doorstromingfouten in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_doorstroming_id_mapping(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/doorstromingidmapping',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download doorstroming id mapping in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_doorstroming_statistieken(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/doorstromingsstatistieken',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download doorstromingsstatistieken in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_genegeerde_data(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/genegeerdedata',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download genegeerdedata in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_validatiefouten(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/validatiefouten',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download validatiefouten in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_verificatierapport(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self._download_to_file(
            request_handler=self.request_handler,
            url=f'aanleveringen/{aanlevering_id}/verificatierapport',
            not_found_message=f'Could not find aanlevering {aanlevering_id}.',
            failure_message=f'Could not download verificatierapport in {aanlevering_id}.',
            file_name=file_name,
            dir_path=dir_path,
        )
