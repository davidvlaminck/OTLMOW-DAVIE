import logging
from pathlib import Path

from otlmow_davie.DavieInternalRestClient import DavieInternalRestClient
from otlmow_davie.Enums import Environment, AuthType

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    settings_path = Path('/home/davidlinux/Documenten/AWV/resources/settings_TypeTemplateProcessor.json')
    rest_client = DavieInternalRestClient(settings_path=settings_path, auth_type=AuthType.COOKIE,
                                                  env=Environment.PRD, use_services=False, cookie='')

    zoek_dict = {
        "aanvragers":
        [
            "14725576-0076-4ea2-b84b-a6a7af20f6cb", "8778c991-5b9d-418d-b38b-28b8fe7c3f06"
        ],
    }
    for x in rest_client.zoek_aanleveringen(search_dict=zoek_dict):
        print(x.aanleveringnummer)

