import logging
from pathlib import Path

from otlmow_davie.DavieClient import DavieClient

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    settings_path = Path('settings_sample.json')
    davie_client = DavieClient(settings_path=settings_path, auth_type='JWT', env='tei')
