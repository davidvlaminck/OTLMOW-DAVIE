import datetime
import pathlib
import shelve
import time
from pathlib import Path
from typing import Optional

from otlmow_davie.DavieDomain import AanleveringCreatie, Aanlevering, AanleveringCreatieMedewerker, \
    AsIsAanvraagCreatie, AsIsAanvraag, AanleveringCreatieOpdrachtnemer, AanleveringCreatieControlefiche
from otlmow_davie.DavieRestClient import DavieRestClient
from otlmow_davie.Enums import Environment, AanleveringStatus, AanleveringSubstatus, \
    LevelOfGeometry, ExportType, AuthType
from otlmow_davie.RequesterFactory import RequesterFactory

this_directory = Path(__file__).parent


class DavieClient:
    def __init__(self, settings_path: Path, auth_type: AuthType, environment: Environment, cookie: str = None,
                 shelve_path: Path = Path(this_directory / 'shelve')):
        self.requester = RequesterFactory.create_requester(auth_type=auth_type, env=environment,
                                                           settings_path=settings_path,
                                                           cookie=cookie)
        self.requester.first_part_url += ''
        self.rest_client = DavieRestClient(requester=self.requester)


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

    def create_aanlevering_controlefiche(self, niveau: str, referentie: str, verificatorId: str, besteknummer: str = None,
                                    bestekomschrijving: str = None, dienstbevelnummer: str = None,
                                    dienstbevelomschrijving: str = None, dossiernummer: str = None
                                    ) -> Aanlevering:
        nieuwe_aanlevering = AanleveringCreatieControlefiche(
            niveau=niveau, referentie=referentie, verificatorId=verificatorId, besteknummer=besteknummer,
            bestekomschrijving=bestekomschrijving, dienstbevelnummer=dienstbevelnummer,
            dienstbevelomschrijving=dienstbevelomschrijving, dossiernummer=dossiernummer)
        return self._create_aanlevering(nieuwe_aanlevering)

    def create_aanlevering(self, ondernemingsnummer: str, besteknummer: str, dossiernummer: str,
                           referentie: str, dienstbevelnummer: str = None, nota: str = None) -> Aanlevering:
        nieuwe_aanlevering = AanleveringCreatieOpdrachtnemer(
            ondernemingsnummer=ondernemingsnummer, besteknummer=besteknummer, dossiernummer=dossiernummer,
            referentie=referentie, dienstbevelnummer=dienstbevelnummer, nota=nota)
        return self._create_aanlevering(nieuwe_aanlevering)

    def create_aanvraag_as_is(self, aanlevering_id: str, asset_types: [str],
                              l_o_g: LevelOfGeometry = LevelOfGeometry.ALLES,
                              email: str = None, geometrie: str = None,
                              export_type: str = ExportType.XLSX) -> AsIsAanvraag:
        as_is_aanvraag_create = AsIsAanvraagCreatie(assetTypes=asset_types, levelOfGeometry=l_o_g, email=email,
                                                    geometrie=geometrie, exportType=export_type)
        as_is_aanvraag = self.rest_client.create_aanvraag_as_is(aanlevering_id, as_is_aanvraag_create)
        self._track_as_is_aanvraag(aanlevering_id, export_type)
        return as_is_aanvraag

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
                        nummer: Optional[str] = None, substatus: Optional[AanleveringSubstatus] = None,
                        as_is_aanvraag: Optional[str] = None, ) -> None:
        with shelve.open(str(self.shelve_path), writeback=True) as db:
            if id not in db.keys():
                db[id] = {'created': datetime.datetime.utcnow()}
            if nummer is not None:
                db[id]['nummer'] = nummer
            if status is not None:
                db[id]['status'] = status
            if substatus is not None:
                db[id]['substatus'] = substatus
            if as_is_aanvraag is not None:
                db[id]['as_is_aanvraag'] = as_is_aanvraag
            # auto prune
            for id in db.keys():
                if db[id]['created'] + datetime.timedelta(days=1) < datetime.datetime.utcnow():
                    del db[id]

            self.db = dict(db)

    def _show_shelve(self) -> None:
        for key in self.db.keys():
            print(f'{key}: {self.db[key]}')

    def _track_aanlevering(self, aanlevering: Aanlevering):
        self._save_to_shelve(id=aanlevering.id, nummer=aanlevering.nummer,
                             status=aanlevering.status, substatus=aanlevering.substatus)

    def _track_as_is_aanvraag(self, aanlevering_id: str, as_is_aanvraag: ExportType):
        self._save_to_shelve(id=aanlevering_id, as_is_aanvraag=as_is_aanvraag)

    def upload_file(self, id: str, file_path: Path):
        if not Path.is_file(file_path):
            raise FileExistsError(f'file does not exist: {file_path}')
        return self.rest_client.upload_file(id=id, file_path=file_path)

    def wait_and_download_as_is_result(self, aanlevering_id: str, interval: int = 10, dir_path: Path = None) -> bool:
        if dir_path is None:
            dir_path = Path(__file__).parent
        while True:
            self.track_aanlevering_by_id(aanlevering_id)
            self._show_shelve()
            if self.db[aanlevering_id]['status'] != AanleveringStatus.DATA_AANGEVRAAGD:
                RuntimeError(f"{aanlevering_id} has status {self.db[aanlevering_id]['status']} instead of DATA_AANGEVRAAGD")

            if self.db[aanlevering_id]['substatus'] != AanleveringSubstatus.BESCHIKBAAR and \
                    self.db[aanlevering_id]['substatus'] == AanleveringSubstatus.LOPEND:
                RuntimeError(f"{aanlevering_id} has substatus {self.db[aanlevering_id]['status']} instead of LOPEND or BESCHIKBAAR")

            if self.db[aanlevering_id]['substatus'] == AanleveringSubstatus.BESCHIKBAAR:
                print(f"as-is aanvraag is reeds beschikbaar voor download, gebruikt download_as_is_result")

            time.sleep(interval)

        # download
        file_format = self.db[aanlevering_id]['as_is_aanvraag']
        file_name = self.db[aanlevering_id]['nummer'] + '.' + file_format
        self.rest_client.download_as_is_result(aanlevering_id=aanlevering_id, dir_path=dir_path, file_name=file_name)
        return True

    def download_as_is_result(self, aanlevering_id: str, dir_path: Path = None) -> bool:
        if dir_path is None:
            dir_path = Path(__file__).parent

        file_format = self.db[aanlevering_id]['as_is_aanvraag']
        file_name = self.db[aanlevering_id]['nummer'] + '.' + file_format
        self.rest_client.download_as_is_result(aanlevering_id=aanlevering_id, dir_path=dir_path, file_name=file_name)
        return True

    def finalize_and_wait(self, id: str, interval: int = 10) -> bool:
        self.track_aanlevering_by_id(id)
        if self.db[id]['status'] == AanleveringStatus.DATA_AANGELEVERD and self.db[id][
            'substatus'] == AanleveringSubstatus.AANGEBODEN:
            return True
        if self.db[id]['status'] not in [
            AanleveringStatus.DATA_AANGELEVERD,
            AanleveringStatus.IN_OPMAAK,
        ] and not(self.db[id]['status'] == AanleveringStatus.DATA_AANGEVRAAGD and self.db[id]['substatus'] ==
                  AanleveringSubstatus.BESCHIKBAAR):
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
