from pathlib import Path

from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.Enums import AuthenticationType, Environment

THIS_DIR = Path(__file__).parent


def test_init_client(subtests):
    settings_path = Path(THIS_DIR / 'settings_unittests.json')
    with subtests.test(msg='JWT tei'):
        davie_client = DavieClient(settings_path=settings_path, auth_type=AuthenticationType.JWT,
                                   environment=Environment.tei)
        assert davie_client is not None
        assert davie_client.rest_client is not None

    with subtests.test(msg='cert prd'):
        davie_client = DavieClient(settings_path=settings_path, auth_type=AuthenticationType.cert,
                                   environment=Environment.prd)
        assert davie_client is not None
        assert davie_client.rest_client is not None

