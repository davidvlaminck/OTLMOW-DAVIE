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

    nieuwe_aanlevering = AanleveringCreatieMedewerker(
        niveau = 'LOG-1',
        referentie = 'b2b integratie test 1',
        verificatorId = '6c2b7c0a-11a9-443a-a96b-a1bec249c629')

    aanlevering = davie_client.create_aanlevering_employee(verificatorId='6c2b7c0a-11a9-443a-a96b-a1bec249c629',
                                                           niveau='LOG-1', referentie='demo otlmow-davie')
    # aanlevering = davie_client.create_aanlevering(ondernemingsnummer='0687738908', besteknummer='1M2D8F/19/42',
    #                                               dossiernummer='X21/0/480', referentie='conversie test 1')

    aanvraag_as_is = davie_client.create_aanvraag_as_is(
        aanlevering_id=aanlevering.id, export_type=ExportType.JSON,
        asset_types=['https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast'],
        geometrie='POLYGON((110000 185000, 111000 185000, 111000 190000, 110000 190000, 110000 185000))')

    davie_client.wait_and_download_as_is_result(aanlevering_id=aanlevering.id)

    davie_client.upload_file(id=aanlevering.id,
                             file_path=Path('type_template_1_mast.json'))
    davie_client.finalize_and_wait(id=aanlevering.id)
