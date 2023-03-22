import logging
import time
from pathlib import Path

from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.Enums import AuthenticationType, Environment

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    settings_path = Path('settings_sample.json')
    davie_client = DavieClient(settings_path=settings_path, auth_type=AuthenticationType.JWT,
                               environment=Environment.dev)

    davie_client._show_shelve()


    aanlevering = davie_client.create_aanlevering_employee(
        niveau='LOG-1', referentie='b2b integratie test 2', verificatorId='6c2b7c0a-11a9-443a-a96b-a1bec249c629')
    davie_client.upload_file(id=aanlevering.id, file_path=Path('type_template_2_buizen.json'))
    davie_client.finalize_and_wait(id=aanlevering.id)


    # print(davie_client.get_aanlevering('88f2bee0-8c71-469b-9393-33614ddd9e6a'))

    # nieuwe_aanlevering = AanleveringCreatieMedewerker(
    #     niveau = 'LOG-1',
    #     referentie = 'b2b integratie test 1',
    #     verificatorId = '6c2b7c0a-11a9-443a-a96b-a1bec249c629')
    #
    # davie_client.create_aanlevering(nieuwe_aanlevering)

#
# id='73de57c1-d253-40f0-9ca1-41f8f46d3be1' nummer='DA-2023-00261' status=<AanleveringStatus.DATA_AANGELEVERD: 'DATA_AANGELEVERD'> substatus=<AanleveringSubstatus.LOPEND: 'LOPEND'>
# id='73de57c1-d253-40f0-9ca1-41f8f46d3be1' nummer='DA-2023-00261' status=<AanleveringStatus.DATA_AANGELEVERD: 'DATA_AANGELEVERD'> substatus=<AanleveringSubstatus.AANGEBODEN: 'AANGEBODEN'>
