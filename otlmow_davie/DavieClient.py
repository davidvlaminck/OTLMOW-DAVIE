from pathlib import Path

from otlmow_davie.DavieRestClient import DavieRestClient
from otlmow_davie.Enums import Environment, AuthenticationType
from otlmow_davie.RequestHandler import RequestHandler
from otlmow_davie.RequesterFactory import RequesterFactory
from otlmow_davie.SettingsManager import SettingsManager


class DavieClient:
    def __init__(self, settings_path: Path, auth_type: AuthenticationType, environment: Environment):
        settings_manager = SettingsManager(settings_path=settings_path)
        requester = RequesterFactory.create_requester(settings=settings_manager.settings, auth_type=auth_type, environment=environment)
        request_handler = RequestHandler(requester=requester)
        self.rest_client = DavieRestClient(request_handler=request_handler)
