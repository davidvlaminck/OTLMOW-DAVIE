import logging
from pathlib import Path

from otlmow_davie.DavieClient import DavieClient
from otlmow_davie.Enums import AuthType, Environment, ExportType

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    settings_path = Path('/home/davidlinux/Documenten/AWV/resources/settings_SyncOTLDataToLegacy.json')
    davie_client = DavieClient(
        settings_path=settings_path,
        auth_type=AuthType.JWT,
        environment=Environment.DEV,
    )

    filename_bad = Path('DA-2025-02128_export.geojson')
    resumable_identifier = 'DA-2026-00942'

    resumable_aanlevering = davie_client.get_resumable_aanlevering(resumable_identifier)


    # resumable_aanlevering.upload_file(file_path=filename_bad)
    # resumable_aanlevering.finalize_and_wait(interval=10)

    # manueel fout  bestand weghalen

    filename_good= Path('voorbeeld.json')
    resumable_aanlevering.upload_file(file_path=filename_good)
    resumable_aanlevering.finalize_and_wait(interval=10)