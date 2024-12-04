import logging
import time
from pathlib import Path

from otlmow_davie.DavieInternalRestClient import DavieInternalRestClient
from otlmow_davie.Enums import AuthenticationType, Environment
from otlmow_davie.RequestHandler import RequestHandler
from otlmow_davie.RequesterFactory import RequesterFactory
from otlmow_davie.SettingsManager import SettingsManager

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    settings_path = Path('/home/davidlinux/Documents/AWV/resources/settings_TypeTemplateProcessor.json')
    settings_manager = SettingsManager(settings_path=settings_path)
    requester = RequesterFactory.create_requester(settings=settings_manager.settings, auth_type=AuthenticationType.JWT,
                                                  environment=Environment.prd, use_services=False)
    request_handler = RequestHandler(requester=requester)
    rest_client = DavieInternalRestClient(request_handler=request_handler)

    for x in rest_client.zoek_aanleveringen():
        print(x)

