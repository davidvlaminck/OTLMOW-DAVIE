from pathlib import Path

import pytest

from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.Enums import AuthType, Environment

THIS_DIR = Path(__file__).parent


@pytest.fixture
def settings_path():
    return Path(THIS_DIR / 'settings_unittests.json')


def test_init_client_jwt_tei(settings_path):
    davie_client = DavieClient(
        settings_path=settings_path,
        auth_type=AuthType.JWT,
        environment=Environment.TEI,
    )
    assert davie_client is not None
    assert davie_client.rest_client is not None


def test_init_client_cert_prd(settings_path):
    davie_client = DavieClient(
        settings_path=settings_path,
        auth_type=AuthType.JWT,
        environment=Environment.PRD,
    )
    assert davie_client is not None
    assert davie_client.rest_client is not None
