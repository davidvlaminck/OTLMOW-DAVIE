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
    davie_client.track_aanlevering_by_id(aanlevering.id)
    print(f'now tracking {aanlevering.id}')
