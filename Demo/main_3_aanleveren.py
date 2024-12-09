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

    upload_resultaat = davie_client.upload_file(id=aanlevering.id,
                                                file_path=Path(__file__).parent.parent / 'type_template_1_mast.json')
    if upload_resultaat is None:
        print('Upload mislukt')

    davie_client.finalize_and_wait(id=aanlevering.id)
