from pathlib import Path
from unittest.mock import Mock

from otlmow_davie.DavieDomain import Aanlevering
from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.DavieRestClient import DavieRestClient
from otlmow_davie.Enums import AuthenticationType, Environment, AanleveringStatus, AanleveringSubstatus

THIS_DIR = Path(__file__).parent

fake_davie_client = Mock(spec=DavieRestClient)


def fake_get_aanlevering(*arg, **kwarg):
    if kwarg['aanlevering_uuid'] == '00000000-0000-0000-0000-000000000001':
        return Aanlevering(id='00000000-0000-0000-0000-000000000001', nummer='DA-2023-00001',
                           status=AanleveringStatus.IN_OPMAAK, substatus=AanleveringSubstatus.BESCHIKBAAR)


fake_davie_client.get_aanlevering = fake_get_aanlevering


def test_get_aanlevering():
    settings_path = Path(THIS_DIR / 'settings_unittests.json')
    davie_client = DavieClient(settings_path=settings_path, auth_type=AuthenticationType.JWT,
                               environment=Environment.tei)
    davie_client.rest_client = fake_davie_client
    aanlevering = davie_client.rest_client.get_aanlevering(aanlevering_uuid='00000000-0000-0000-0000-000000000001')
    assert aanlevering.id == '00000000-0000-0000-0000-000000000001'
    assert aanlevering.nummer == 'DA-2023-00001'
    assert aanlevering.status == AanleveringStatus.IN_OPMAAK

