import shelve
import time
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
            try:
                import dbm.ndbm
                with dbm.ndbm.open(str(shelve_path), 'c'):
                    pass
            except ModuleNotFoundError:
                with shelve.open(str(shelve_path)):
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

    def track_aanlevering_by_id(self, id: str):
        aanlevering = self.get_aanlevering(id=id)
        self._track_aanlevering(aanlevering)

    def get_aanlevering(self, id: str) -> Aanlevering:
        return self.rest_client.get_aanlevering(id=id)

    def _save_to_shelve(self, id: Optional[str], status: Optional[AanleveringStatus] = None,
                        nummer: Optional[str] = None, substatus: Optional[AanleveringSubstatus] = None) -> None:
        with shelve.open(str(self.shelve_path), writeback=True) as db:
            if id not in db.keys():
                db[id] = {}
            if nummer is not None:
                db[id]['nummer'] = nummer
            if status is not None:
                db[id]['status'] = status
            if substatus is not None:
                db[id]['substatus'] = substatus
            self.db = dict(db)

    def _show_shelve(self) -> None:
        for key in self.db.keys():
            print(f'{key}: {self.db[key]}')

    def _track_aanlevering(self, aanlevering: Aanlevering):
        self._save_to_shelve(id=aanlevering.id, nummer=aanlevering.nummer,
                             status=aanlevering.status, substatus=aanlevering.substatus)

    def upload_file(self, id: str, file_path: Path):
        if not Path.is_file(file_path):
            raise FileExistsError(f'file does not exist: {file_path}')
        self.rest_client.upload_file(id=id, file_path=file_path)

    def finalize_and_wait(self, id: str, interval: int = 10) -> bool:
        self.track_aanlevering_by_id(id)
        if self.db[id]['status'] == AanleveringStatus.DATA_AANGELEVERD and self.db[id]['substatus'] == AanleveringSubstatus.AANGEBODEN:
            return True
        if self.db[id]['status'] != AanleveringStatus.DATA_AANGELEVERD and self.db[id]['status'] != AanleveringStatus.IN_OPMAAK:
            raise RuntimeError(f"{id} has status {self.db[id]['status']} instead of IN_OPMAAK / DATA_AANGELEVERD")

        if AanleveringStatus.IN_OPMAAK:
            self.rest_client.finalize(id=id)

        while True:
            self.track_aanlevering_by_id(id)
            self._show_shelve()
            if 'substatus' in self.db[id] and self.db[id]['substatus'] != AanleveringSubstatus.LOPEND:
                break
            time.sleep(interval)

        return True

