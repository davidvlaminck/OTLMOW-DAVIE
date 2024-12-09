import logging
from pathlib import Path

from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.DavieDomain import AanleveringCreatieMedewerker
from otlmow_davie.Enums import Environment, ExportType, AuthType

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    settings_path = Path('/home/davidlinux/Documents/AWV/resources/settings_SyncOTLDataToLegacy.json')
    davie_client = DavieClient(environment=Environment.TEI, auth_type=AuthType.JWT, settings_path=settings_path)

    aanlevering_id = '57633de5-a569-4cd6-84c5-231ce693fff9'

    aanlevering = davie_client.get_aanlevering(aanlevering_id)

    aanvraag_as_is = davie_client.create_aanvraag_as_is(
        aanlevering_id=aanlevering.id, export_type=ExportType.JSON,
        asset_types=['https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast'],
        geometrie='POLYGON((110000 185000, 111000 185000, 111000 190000, 110000 190000, 110000 185000))')

    davie_client.wait_and_download_as_is_result(aanlevering_id=aanlevering.id)
