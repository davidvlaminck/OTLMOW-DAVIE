import dbm.ndbm
import shelve
from pathlib import Path
from typing import Optional

from otlmow_davie.DavieDomain import AanleveringCreatie, Aanlevering, AanleveringCreatieMedewerker
from otlmow_davie.DavieRestClient import DavieRestClient
from otlmow_davie.Enums import Environment, AuthenticationType, AanleveringStatus, AanleveringSubstatus
from otlmow_davie.RequestHandler import RequestHandler
from otlmow_davie.RequesterFactory import RequesterFactory
from otlmow_davie.SettingsManager import SettingsManager

this_directory = Path(__file__).parent


class DavieClient:
    def __init__(self, settings_path: Path, auth_type: AuthenticationType, environment: Environment,
                 shelve_path: Path = Path(this_directory / 'shelve')):
        settings_manager = SettingsManager(settings_path=settings_path)
        requester = RequesterFactory.create_requester(settings=settings_manager.settings, auth_type=auth_type,
                                                      environment=environment)
        request_handler = RequestHandler(requester=requester)
        self.rest_client = DavieRestClient(request_handler=request_handler)
        if not Path.is_file(shelve_path):
            with dbm.ndbm.open(str(shelve_path), 'c'):
                pass
        self.shelve_path = shelve_path

    def create_aanlevering_employee(self, niveau: str, referentie: str, verificatorId: str, besteknummer: str = None,
                                    bestekomschrijving: str = None, dienstbevelnummer: str = None,
                                    dienstbevelomschrijving: str = None, dossiernummer: str = None, nota: str = None
                                    ) -> Aanlevering:
        nieuwe_aanlevering = AanleveringCreatieMedewerker(
            niveau=niveau, referentie=referentie, verificatorId=verificatorId, besteknummer=besteknummer,
            bestekomschrijving=bestekomschrijving, dienstbevelnummer=dienstbevelnummer,
            dienstbevelomschrijving=dienstbevelomschrijving, dossiernummer=dossiernummer, nota=nota)
        return self._create_aanlevering(nieuwe_aanlevering)

    def create_aanlevering(self, ondernemingsnummer: str, besteknummer: str, dossiernummer: str,
                           referentie: str, dienstbevelnummer: str = None, nota: str = None) -> Aanlevering:
        nieuwe_aanlevering = AanleveringCreatieMedewerker(
            ondernemingsnummer=ondernemingsnummer, besteknummer=besteknummer, dossiernummer=dossiernummer,
            referentie=referentie, dienstbevelnummer=dienstbevelnummer, nota=nota)
        return self._create_aanlevering(nieuwe_aanlevering)

    def _create_aanlevering(self, nieuwe_aanlevering: AanleveringCreatie) -> Aanlevering:
        aanlevering = self.rest_client.create_aanlevering(nieuwe_aanlevering)
        self._track_aanlevering(aanlevering)
        return aanlevering

    def track_aanlevering_by_uuid(self, aanlevering_uuid: str):
        aanlevering = self.get_aanlevering(aanlevering_uuid)
        self._track_aanlevering(aanlevering)

    def get_aanlevering(self, aanlevering_uuid: str) -> Aanlevering:
        return self.rest_client.get_aanlevering(aanlevering_uuid)

    def _save_to_shelve(self, aanlevering_id: Optional[str], status: Optional[AanleveringStatus] = None,
                        nummer: Optional[str] = None, substatus: Optional[AanleveringSubstatus] = None) -> None:
        with shelve.open(str(self.shelve_path), writeback=True) as db:
            if aanlevering_id not in db.keys():
                db[aanlevering_id] = {}
            if nummer is not None:
                db[aanlevering_id]['nummer'] = nummer
            if status is not None:
                db[aanlevering_id]['status'] = status
            if substatus is not None:
                db[aanlevering_id]['substatus'] = substatus

    def _show_shelve(self) -> None:
        with shelve.open(str(self.shelve_path)) as db:
            for key in db.keys():
                print(f'{key}: {db[key]}')

    def _track_aanlevering(self, aanlevering: Aanlevering):
        self._save_to_shelve(aanlevering_id=aanlevering.id, nummer=aanlevering.nummer,
                             status=aanlevering.status, substatus=aanlevering.substatus)
