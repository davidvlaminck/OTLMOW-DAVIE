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

    settings_path = Path('/home/davidlinux/Documents/AWV/resources/settings_TypeTemplateProcessor.json')
    davie_client = DavieClient(settings_path=settings_path,
                               auth_type=AuthenticationType.JWT,
                               environment=Environment.tei)

    # aanlevering = davie_client.create_aanlevering_employee(
    #     niveau='LOG-1', referentie='as-is test 1',
    #     verificatorId='6c2b7c0a-11a9-443a-a96b-a1bec249c629')

    aanvraag_as_is = davie_client.create_aanvraag_as_is(
        aanlevering_id='3d16b7b0-5548-427d-80f6-1cb042a9487f',
        asset_types=['https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#WVLichtmast'],
        geometrie='POLYGON((109000 180000, 111000 180000, 111000 190000, 109000 190000, 109000 180000))')

    davie_client.wait_and_download_as_is_result(aanlevering_id='3d16b7b0-5548-427d-80f6-1cb042a9487f')

    # davie_client.upload_file(id=aanlevering.id,
    #                          file_path=Path('type_template_30_masten.json'))
    # davie_client.finalize_and_wait(id=aanlevering.id)
    #

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
