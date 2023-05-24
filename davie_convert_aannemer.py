import logging
import time
from pathlib import Path

from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.Enums import AuthenticationType, Environment

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    settings_path = Path('/home/davidlinux/Documents/AWV/resources/settings_davie.json')
    davie_client = DavieClient(settings_path=settings_path,
                               auth_type=AuthenticationType.JWT,
                               environment=Environment.tei)

    aanlevering = davie_client.create_aanlevering(ondernemingsnummer='0687738908', besteknummer='1M2D8F/19/42',
                                                  dossiernummer='X21/0/480', referentie='conversie test 1')
    davie_client.upload_file(id=aanlevering.id, file_path=Path('some_file.sdf'))
    davie_client.finalize_and_wait(id=aanlevering.id)

    aanvraag_as_is = davie_client.create_aanvraag_as_is(aanlevering_id=aanlevering.id,
        asset_types=['https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#RechteSteun'],
        geometrie='POLYGON((109000 180000, 111000 180000, 111000 190000, 109000 190000, 109000 180000))')
    davie_client.wait_and_download_as_is_result(aanlevering_id=aanlevering.id)
