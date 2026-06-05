import logging
from pathlib import Path

from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.Enums import AuthType, Environment, ExportType

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    settings_path = Path('/home/davidlinux/Documenten/AWV/resources/settings_SyncOTLDataToLegacy.json')
    davie_client = DavieClient(
        settings_path=settings_path,
        auth_type=AuthType.JWT,
        environment=Environment.DEV,
    )



    aanlevering = davie_client.create_aanlevering_employee(verificatorId='6c2b7c0a-11a9-443a-a96b-a1bec249c629',
                                                           niveau='LOG-1', referentie='demo otlmow-davie')

    aanvraag_as_is = davie_client.create_aanvraag_as_is(
        aanlevering_id=aanlevering.id,
        export_type=ExportType.JSON,
        asset_types=['https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast'],
        geometrie='POLYGON((110000 185000, 111000 185000, 111000 190000, 110000 190000, 110000 185000))')

    # Poll until the as-is export is ready and download it when available.
    davie_client.wait_and_download_as_is_result(
        aanlevering_id=aanlevering.id,
        interval=10,
        dir_path=Path('.'),
    )
