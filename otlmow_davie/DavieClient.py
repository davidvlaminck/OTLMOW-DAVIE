import datetime
from dataclasses import dataclass
import pathlib
import shelve
import time
import logging
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from otlmow_davie.DavieDomain import AanleveringCreatie, Aanlevering, AanleveringCreatieMedewerker, \
    AsIsAanvraagCreatie, AsIsAanvraag, AanleveringCreatieOpdrachtnemer, AanleveringCreatieControlefiche, \
    LosseValidatie, LosseValidatieBestandResultaat
from otlmow_davie.DavieRestClient import DavieRestClient
from otlmow_davie.Enums import Environment, AuthType, AanleveringStatus, AanleveringSubstatus, \
    LevelOfGeometry, ExportType
from otlmow_davie.RequestHandler import RequestHandler
from otlmow_davie.RequesterFactory import RequesterFactory

this_directory = Path(__file__).parent

# Substatus sets used during polling
_PENDING_SUBSTATUS = {None, AanleveringSubstatus.LOPEND}
_TERMINAL_SUCCESS_SUBSTATUS = {
    AanleveringSubstatus.AANGEBODEN,
    AanleveringSubstatus.GOEDGEKEURD,
}
_RECOVERABLE_SUCCESS_SUBSTATUS = {
    AanleveringSubstatus.BESCHIKBAAR,
}
_SUCCESS_SUBSTATUS = _TERMINAL_SUCCESS_SUBSTATUS | _RECOVERABLE_SUCCESS_SUBSTATUS
_FAILURE_SUBSTATUS = {
    AanleveringSubstatus.GEFAALD,
    AanleveringSubstatus.AFGEKEURD,
    AanleveringSubstatus.OPGESCHORT,
}
_RESUMABLE_STATUS = {
    AanleveringStatus.IN_OPMAAK,
    AanleveringStatus.DATA_AANGELEVERD,
    AanleveringStatus.DATA_AANGEVRAAGD,
}
_TERMINAL_STATUS = {
    AanleveringStatus.GEANNULEERD,
    AanleveringStatus.VERVALLEN,
}
_PRUNE_AFTER = datetime.timedelta(days=7)

_CONSOLE = Console()
_PINGPONG_WIDTH = 5


def _pingpong_frame(step: int, width: int = _PINGPONG_WIDTH) -> str:
    """Return a pingpong-ball frame moving left-to-right and back."""
    if width <= 1:
        return 'o'

    cycle = (width * 2) - 2
    pos = step % cycle
    if pos >= width:
        pos = cycle - pos
    return (' ' * pos) + 'o' + (' ' * (width - 1 - pos))


def _substatus_style(substatus) -> str:
    if substatus in _SUCCESS_SUBSTATUS:
        return 'bold green'
    if substatus in _FAILURE_SUBSTATUS:
        return 'bold red'
    return 'bold yellow'


def _make_poll_panel(entry: dict, aanlevering_id: str, title: str,
                     elapsed: int, frame: str, interval: int) -> Panel:
    status = entry.get('status', '—')
    substatus = entry.get('substatus')
    nummer = entry.get('nummer', aanlevering_id)

    status_str = status.value if hasattr(status, 'value') else str(status)
    substatus_str = substatus.value if hasattr(substatus, 'value') else str(substatus) if substatus else '—'

    tbl = Table.grid(padding=(0, 2))
    tbl.add_column(style='dim')
    tbl.add_column()
    tbl.add_row('Aanlevering', str(nummer))
    tbl.add_row('ID', aanlevering_id)
    tbl.add_row('Status', status_str)
    tbl.add_row('Substatus', Text(substatus_str, style=_substatus_style(substatus)))
    tbl.add_row('Verstreken', f'{elapsed}s')

    subtitle = Text(f'{frame} polling elke {interval}s', style='cyan')
    return Panel(tbl, title=f'[bold]{title}[/bold]', subtitle=subtitle)


@dataclass(slots=True)
class ResumableAanlevering:
    """Lightweight wrapper around a DAVIE aanlevering for explicit resume flows.

    This keeps the DAVIE domain model unchanged while still offering convenience
    methods for upload/finalize/wait on a selected resumable job.
    """

    client: 'DavieClient'
    aanlevering: Aanlevering

    def __getattr__(self, item):
        return getattr(self.aanlevering, item)

    def refresh(self) -> 'ResumableAanlevering':
        self.aanlevering = self.client.get_aanlevering(id=self.aanlevering.id)
        self.client._track_aanlevering(self.aanlevering)
        return self

    @property
    def is_restartable(self) -> bool:
        """True when the aanlevering ended with a failure substatus and needs a re-upload."""
        return self.aanlevering.substatus in _FAILURE_SUBSTATUS

    def upload_file(self, file_path: Path):
        if self.is_restartable:
            _CONSOLE.print(
                f'[dim]ℹ  Uploaden van gecorrigeerd bestand naar gefaalde aanlevering '
                f'[cyan]{self.aanlevering.nummer or self.aanlevering.id}[/cyan] …[/dim]'
            )
        self.client.upload_file(id=self.aanlevering.id, file_path=file_path)
        return self

    def finalize_and_wait(self, interval: int = 10) -> bool:
        return self.client.finalize_and_wait(id=self.aanlevering.id, interval=interval)

    def wait_and_download_as_is_result(self, interval: int = 10, dir_path: Optional[Path] = None) -> bool:
        return self.client.wait_and_download_as_is_result(
            aanlevering_id=self.aanlevering.id,
            interval=interval,
            dir_path=dir_path,
        )


class DavieClient:
    def __init__(self, settings_path: Path, auth_type: AuthType, environment: Environment,
                 shelve_path: Path = Path(this_directory / 'shelve'), use_services: bool = True,
                 api_prefix: str = ''):
        requester = RequesterFactory.create_requester(settings_path=settings_path, auth_type=auth_type,
                                                      env=environment, use_services=use_services)
        request_handler = RequestHandler(requester=requester)
        self.rest_client = DavieRestClient(request_handler=request_handler, api_prefix=api_prefix)
        if not Path.is_file(shelve_path):
            try:
                import dbm.ndbm
                with dbm.ndbm.open(str(shelve_path), 'c'):
                    pass
            except ModuleNotFoundError:
                with shelve.open(str(shelve_path)):
                    pass

        self.shelve_path = shelve_path
        self.db: dict = {}

    def _load_shelve_snapshot(self) -> dict[str, dict[str, Any]]:
        with shelve.open(str(self.shelve_path)) as db:
            self.db = dict(db)
        return self.db

    @staticmethod
    def _is_terminal_entry(status: Optional[AanleveringStatus], substatus: Optional[AanleveringSubstatus]) -> bool:
        if status in _TERMINAL_STATUS:
            return True
        if substatus in _TERMINAL_SUCCESS_SUBSTATUS or substatus in _FAILURE_SUBSTATUS:
            return True
        return False

    def create_aanlevering_employee(self, niveau: str, referentie: str, verificatorId: str,
                                    besteknummer: Optional[str] = None,
                                    bestekomschrijving: Optional[str] = None,
                                    dienstbevelnummer: Optional[str] = None,
                                    dienstbevelomschrijving: Optional[str] = None,
                                    dossiernummer: Optional[str] = None,
                                    nota: Optional[str] = None
                                    ) -> Aanlevering:
        nieuwe_aanlevering = AanleveringCreatieMedewerker(
            niveau=niveau, referentie=referentie, verificatorId=verificatorId, besteknummer=besteknummer,
            bestekomschrijving=bestekomschrijving, dienstbevelnummer=dienstbevelnummer,
            dienstbevelomschrijving=dienstbevelomschrijving, dossiernummer=dossiernummer, nota=nota)
        return self._create_aanlevering(nieuwe_aanlevering)

    def create_aanlevering_controlefiche(self, referentie: str,
                                         ondernemingsnummer: Optional[str] = None,
                                         besteknummer: Optional[str] = None,
                                         dienstbevelnummer: Optional[str] = None,
                                         dossiernummer: Optional[str] = None,
                                    ) -> Aanlevering:
        nieuwe_aanlevering = AanleveringCreatieControlefiche(
            referentie=referentie, ondernemingsnummer=ondernemingsnummer, besteknummer=besteknummer,
            dienstbevelnummer=dienstbevelnummer, dossiernummer=dossiernummer)
        return self._create_aanlevering(nieuwe_aanlevering)

    def create_aanlevering(self, ondernemingsnummer: str, besteknummer: str, dossiernummer: str,
                           referentie: str, dienstbevelnummer: Optional[str] = None,
                           nota: Optional[str] = None) -> Aanlevering:
        nieuwe_aanlevering = AanleveringCreatieOpdrachtnemer(
            ondernemingsnummer=ondernemingsnummer, besteknummer=besteknummer, dossiernummer=dossiernummer,
            referentie=referentie, dienstbevelnummer=dienstbevelnummer, nota=nota)
        return self._create_aanlevering(nieuwe_aanlevering)

    def create_aanvraag_as_is(self, aanlevering_id: str, asset_types: list[str],
                              l_o_g: LevelOfGeometry = LevelOfGeometry.ALLES,
                              email: Optional[str] = None, geometrie: Optional[str] = None,
                              export_type: ExportType = ExportType.XLSX) -> AsIsAanvraag:
        as_is_aanvraag_create = AsIsAanvraagCreatie(assetTypes=asset_types, levelOfGeometry=l_o_g,
                                                    emailAdres=email, geometrie=geometrie,
                                                    exportType=export_type)
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

    def _save_to_shelve(self, id: str, status: Optional[AanleveringStatus] = None,
                        nummer: Optional[str] = None, substatus: Optional[AanleveringSubstatus] = None,
                        as_is_aanvraag: Optional[str] = None) -> None:
        with shelve.open(str(self.shelve_path), writeback=True) as db:
            if id not in db.keys():
                db[id] = {'created': datetime.datetime.now(datetime.UTC)}
            db[id]['updated'] = datetime.datetime.now(datetime.UTC)
            if nummer is not None:
                db[id]['nummer'] = nummer
            if status is not None:
                db[id]['status'] = status
            if substatus is not None:
                db[id]['substatus'] = substatus
            if as_is_aanvraag is not None:
                db[id]['as_is_aanvraag'] = as_is_aanvraag
            # Auto-prune terminal entries after one week (handles legacy naive datetimes).
            now_utc = datetime.datetime.now(datetime.UTC)
            for key in list(db.keys()):
                created = db[key].get('created')
                if created is None:
                    continue
                if created.tzinfo is None:
                    created = created.replace(tzinfo=datetime.UTC)
                existing_status = db[key].get('status')
                existing_substatus = db[key].get('substatus')
                is_terminal = self._is_terminal_entry(status=existing_status, substatus=existing_substatus)
                if is_terminal and created + _PRUNE_AFTER < now_utc:
                    del db[key]

            self.db = dict(db)

    def list_resumable_aanleveringen(self) -> list[dict[str, Any]]:
        """Return resumable entries from shelve, newest first.

        An entry is resumable when it is in an active DAVIE status and has no terminal substatus yet.
        Entries with a failure substatus (GEFAALD, AFGEKEURD, OPGESCHORT) are included as
        'restartable': the user can delete the faulty file(s) and re-upload.
        """
        snapshot = self._load_shelve_snapshot()
        resumable: list[dict[str, Any]] = []

        for aanlevering_id, entry in snapshot.items():
            status = entry.get('status')
            substatus = entry.get('substatus')
            if status not in _RESUMABLE_STATUS:
                continue
            is_failed = substatus in _FAILURE_SUBSTATUS
            # Skip entries that finished successfully – those are truly done.
            if not is_failed and self._is_terminal_entry(status=status, substatus=substatus):
                continue

            created = entry.get('created')
            if created is not None and created.tzinfo is None:
                created = created.replace(tzinfo=datetime.UTC)
            prune_at = created + _PRUNE_AFTER if created is not None else None

            resumable.append({
                'id': aanlevering_id,
                'created': created,
                'updated': entry.get('updated'),
                'nummer': entry.get('nummer'),
                'status': status,
                'substatus': substatus,
                'as_is_aanvraag': entry.get('as_is_aanvraag'),
                'restartable': is_failed,
                'prune_at': prune_at,
            })

        resumable.sort(
            key=lambda item: item.get('updated') or item.get('created') or datetime.datetime.min,
            reverse=True,
        )
        return resumable

    def get_resumable_aanlevering(self, identifier: str) -> 'ResumableAanlevering':
        """Return a specific resumable aanlevering by UUID or DA-nummer.

        The returned object is a small wrapper around the API model; it keeps the
        domain model intact while offering convenience methods for explicit resume.

        Aanleveringen with a failure substatus (GEFAALD, AFGEKEURD, OPGESCHORT) are also
        returned so the user can delete faulty bestanden and re-upload a corrected file.
        """
        for entry in self.list_resumable_aanleveringen():
            if identifier not in {entry['id'], entry.get('nummer')}:
                continue

            aanlevering = self.get_aanlevering(id=entry['id'])
            self._track_aanlevering(aanlevering)

            is_failed = aanlevering.substatus in _FAILURE_SUBSTATUS
            if self._is_terminal_entry(aanlevering.status, aanlevering.substatus) and not is_failed:
                raise RuntimeError(
                    f'Aanlevering {identifier} is succesvol afgerond ({aanlevering.status} / '
                    f'{aanlevering.substatus}) en kan niet worden hervat.'
                )

            if is_failed:
                substatus_str = aanlevering.substatus.value if hasattr(aanlevering.substatus, 'value') else str(aanlevering.substatus)
                _CONSOLE.print(
                    f'\n[bold yellow]⚠  Aanlevering [cyan]{aanlevering.nummer or aanlevering.id}[/cyan] '
                    f'heeft substatus [bold red]{substatus_str}[/bold red].[/bold yellow]\n'
                    f'   Verwijder het foutieve bestand via de DAVIE-interface of via:\n'
                    f'   [dim]davie_client.delete_file(aanlevering_id={aanlevering.id!r}, bestand_id=<id>)[/dim]\n'
                    f'   Upload daarna een gecorrigeerd bestand en roep [bold]finalize_and_wait()[/bold] aan.\n'
                )

            return ResumableAanlevering(client=self, aanlevering=aanlevering)

        available = ', '.join(
            f"{item.get('nummer') or item['id']} ({item['id']})"
            + (' [gefaald]' if item.get('restartable') else '')
            for item in self.list_resumable_aanleveringen()
        ) or 'geen'
        raise ValueError(f'Geen resumable aanlevering gevonden voor {identifier!r}. Beschikbaar: {available}.')

    def resume_latest_aanlevering(self, interval: int = 10, dir_path: Optional[Path] = None) -> bool:
        """Resume the most recently tracked active aanlevering.

        - DATA_AANGEVRAAGD: continues waiting and downloads as-is result
        - IN_OPMAAK / DATA_AANGELEVERD: continues finalize polling
        """
        resumable = self.list_resumable_aanleveringen()
        if len(resumable) == 0:
            raise RuntimeError('Geen resumable aanlevering gevonden in shelve.')

        entry = resumable[0]
        aanlevering_id = entry['id']
        # Refresh from API first: shelve is a checkpoint and may be stale after an interrupted run.
        self.track_aanlevering_by_id(id=aanlevering_id)
        entry = self.db.get(aanlevering_id, entry)
        status = entry.get('status')
        substatus = entry.get('substatus')

        if self._is_terminal_entry(status=status, substatus=substatus):
            raise RuntimeError(
                f'Aanlevering {aanlevering_id} is al klaar met status {status} / {substatus}. '
                'Niets te hervatten.'
            )

        if status == AanleveringStatus.DATA_AANGEVRAAGD:
            return self.wait_and_download_as_is_result(
                aanlevering_id=aanlevering_id,
                interval=interval,
                dir_path=dir_path,
            )

        return self.finalize_and_wait(id=aanlevering_id, interval=interval)

    def _track_aanlevering(self, aanlevering: Aanlevering):
        self._save_to_shelve(id=aanlevering.id, nummer=aanlevering.nummer,
                             status=aanlevering.status, substatus=aanlevering.substatus)

    def _track_as_is_aanvraag(self, aanlevering_id: str, as_is_aanvraag: ExportType):
        self._save_to_shelve(id=aanlevering_id, as_is_aanvraag=as_is_aanvraag)

    def _poll_until_done(self, aanlevering_id: str, title: str, interval: int = 10) -> dict:
        """Poll the API every `interval` seconds with in-place animated status line.

        Returns the final shelve entry when a non-pending substatus is reached.
        Uses a pingpong-ball in-place spinner.
        """
        start = time.monotonic()
        frame_idx = 0
        last_poll = start - interval  # trigger an immediate first poll

        entry: dict = self.db.get(aanlevering_id, {})
        nummer = entry.get('nummer', aanlevering_id)

        import sys

        # Print header once.
        try:
            sys.stdout.write(f'\n{title}\n')
            sys.stdout.flush()
        except (AttributeError, IOError):
            pass

        while True:
            now = time.monotonic()
            elapsed = int(now - start)
            frame = _pingpong_frame(frame_idx)

            if now - last_poll >= interval:
                self.track_aanlevering_by_id(aanlevering_id)
                entry = self.db.get(aanlevering_id, {})
                last_poll = now

            status_str = (entry.get('status').value if hasattr(entry.get('status'), 'value')
                          else str(entry.get('status', '—')))
            substatus = entry.get('substatus')
            substatus_str = (substatus.value if hasattr(substatus, 'value')
                             else str(substatus) if substatus else '—')

            status_line = (f'[{frame}] {elapsed}s | Status: {status_str} | Substatus: {substatus_str} | '
                           f'{nummer} ({aanlevering_id})')
            try:
                sys.stdout.write(f'\r{status_line:<120}')
                sys.stdout.flush()
            except (AttributeError, IOError):
                _CONSOLE.print(status_line)

            frame_idx += 1
            if substatus not in _PENDING_SUBSTATUS:
                break

            time.sleep(0.5)

        try:
            sys.stdout.write('\n')
            sys.stdout.flush()
        except (AttributeError, IOError):
            pass

        _CONSOLE.print(_make_poll_panel(entry, aanlevering_id, title, int(now - start),
                                        _pingpong_frame(frame_idx), interval))

        return entry

    def upload_file(self, id: str, file_path: Path):
        if not Path.is_file(file_path):
            raise FileExistsError(f'file does not exist: {file_path}')
        self.rest_client.upload_file(id=id, file_path=file_path)

    def wait_and_download_as_is_result(self, aanlevering_id: str, interval: int = 10,
                                       dir_path: Optional[Path] = None) -> bool:
        if dir_path is None:
            dir_path = pathlib.Path(__file__).parent

        try:
            entry = self._poll_until_done(
                aanlevering_id=aanlevering_id,
                title=f'As-is aanvraag – {aanlevering_id}',
                interval=interval,
            )

            substatus = entry.get('substatus')
            status = entry.get('status')

            if substatus != AanleveringSubstatus.BESCHIKBAAR:
                status_str = status.value if hasattr(status, "value") else str(status)
                substatus_str = substatus.value if hasattr(substatus, "value") else str(substatus)
                _CONSOLE.print(
                    f'\n[bold red]✗ As-is download niet mogelijk[/bold red]\n'
                    f'As-is aanvraag eindigde met status [yellow]{status_str}[/yellow] / [yellow]{substatus_str}[/yellow].\n'
                    f'Verwacht: [green]BESCHIKBAAR[/green]\n'
                )
                return False

            fmt = entry.get('as_is_aanvraag', 'json')
            file_name = entry['nummer'] + '.' + (fmt.value if hasattr(fmt, 'value') else str(fmt))
            self.rest_client.download_as_is_result(aanlevering_id=aanlevering_id,
                                                   dir_path=dir_path, file_name=file_name)
            _CONSOLE.print(f'[bold green]✓[/bold green] As-is resultaat opgeslagen als [cyan]{file_name}[/cyan]')
            return True
        except SystemExit as ex:
            # Convert fatal exits into a clean failure return so callers don't need to catch.
            logging.error('As-is download exited: %s', ex)
            return False
        except Exception:
            logging.exception('Unexpected error while waiting for/downloading as-is result')
            return False

    def finalize_and_wait(self, id: str, interval: int = 10) -> bool:
        # Ensure we have fresh data before deciding whether to finalize.
        self.track_aanlevering_by_id(id)
        entry = self.db[id]
        status = entry.get('status')
        substatus = entry.get('substatus')

        # Already past finalization – nothing left to do.
        if status == AanleveringStatus.DATA_AANGELEVERD and substatus == AanleveringSubstatus.AANGEBODEN:
            _CONSOLE.print(f'[bold green]✓[/bold green] Aanlevering [cyan]{id}[/cyan] is reeds aangeboden.')
            return True

        if status not in {AanleveringStatus.DATA_AANGELEVERD, AanleveringStatus.IN_OPMAAK, AanleveringStatus.DATA_AANGEVRAAGD}:
            status_str = status.value if hasattr(status, "value") else str(status)
            _CONSOLE.print(
                f'\n[bold red]✗ Finaliseren niet mogelijk[/bold red]\n'
                f'Aanlevering [cyan]{id}[/cyan] heeft status [yellow]{status_str}[/yellow] in plaats van IN_OPMAAK / DATA_AANGELEVERD / DATA_AANGEVRAAGD.\n'
            )
            raise SystemExit(1)

        # Explicitly trigger (re)finalization for resumable jobs.
        # This includes failed DATA_AANGELEVERD entries after a corrected re-upload.
        # Allow finalize to be triggered for resumable states. This includes:
        # - IN_OPMAAK / DATA_AANGELEVERD / DATA_AANGEVRAAGD with pending substatus
        # - DATA_AANGELEVERD with a recoverable success substatus (BESCHIKBAAR)
        should_call_finalize = (
            status in {AanleveringStatus.IN_OPMAAK, AanleveringStatus.DATA_AANGELEVERD, AanleveringStatus.DATA_AANGEVRAAGD}
            and substatus in (_PENDING_SUBSTATUS | _FAILURE_SUBSTATUS | _RECOVERABLE_SUCCESS_SUBSTATUS)
        )

        if should_call_finalize:
            try:
                self.rest_client.finalize(id=id)
            except (RuntimeError, ProcessLookupError) as ex:
                # Resume scenario: finalize may already be in progress server-side.
                self.track_aanlevering_by_id(id)
                refreshed = self.db.get(id, {})
                refreshed_status = refreshed.get('status')
                refreshed_substatus = refreshed.get('substatus')
                msg = str(ex).lower()
                can_continue_polling = (
                    ('finaliseerbaar' in msg or 'niet toegelaten' in msg or '403' in msg)
                    and refreshed_status in _RESUMABLE_STATUS
                    and refreshed_substatus in _PENDING_SUBSTATUS
                )
                if can_continue_polling:
                    logging.info(
                        'Finalize for %s returned non-fatal error (%s); continuing with polling.',
                        id,
                        ex,
                    )
                else:
                    raise

        entry = self._poll_until_done(
            aanlevering_id=id,
            title=f'Verwerking aanlevering – {id}',
            interval=interval,
        )

        substatus = entry.get('substatus')
        status = entry.get('status')
        nummer = entry.get('nummer', id)

        if substatus in _FAILURE_SUBSTATUS:
            substatus_str = substatus.value if hasattr(substatus, "value") else str(substatus)
            _CONSOLE.print(
                f'\n[bold red]✗ Verwerking mislukt[/bold red]\n'
                f'Aanlevering [cyan]{nummer}[/cyan] ({id}) is geëindigd met substatus [bold red]{substatus_str}[/bold red].\n'
                f'Controleer de validatiefouten of doorstromingfouten via de API:\n'
                f'  [dim]davie_client.download_validatiefouten(aanlevering_id={id!r}, file_name="...", dir_path=Path("."))[/dim]\n'
                f'  [dim]davie_client.download_doorstromingfouten(aanlevering_id={id!r}, file_name="...", dir_path=Path("."))[/dim]\n'
            )
            raise SystemExit(1)

        if substatus not in _SUCCESS_SUBSTATUS:
            status_str = status.value if hasattr(status, "value") else str(status)
            substatus_str = substatus.value if hasattr(substatus, "value") else str(substatus) if substatus else '—'
            _CONSOLE.print(
                f'\n[bold red]✗ Onverwachte toestand[/bold red]\n'
                f'Aanlevering [cyan]{nummer}[/cyan] ({id}) bereikte toestand: [yellow]{status_str}[/yellow] / [yellow]{substatus_str}[/yellow]\n'
            )
            raise SystemExit(1)

        _CONSOLE.print(
            f'[bold green]✓[/bold green] Aanlevering [cyan]{nummer}[/cyan] afgerond – '
            f'status: [bold]{status}[/bold]  substatus: [bold green]{substatus}[/bold green]'
        )
        return True

    def delete_file(self, aanlevering_id: str, bestand_id: str) -> None:
        self.rest_client.delete_file(aanlevering_id=aanlevering_id, bestand_id=bestand_id)

    def download_as_is_errors(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self.rest_client.download_as_is_errors(aanlevering_id=aanlevering_id, file_name=file_name, dir_path=dir_path)

    def download_doorstromingfouten(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self.rest_client.download_doorstromingfouten(aanlevering_id=aanlevering_id, file_name=file_name, dir_path=dir_path)

    def download_doorstroming_id_mapping(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self.rest_client.download_doorstroming_id_mapping(
            aanlevering_id=aanlevering_id,
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_doorstroming_statistieken(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self.rest_client.download_doorstroming_statistieken(
            aanlevering_id=aanlevering_id,
            file_name=file_name,
            dir_path=dir_path,
        )

    def download_genegeerde_data(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self.rest_client.download_genegeerde_data(aanlevering_id=aanlevering_id, file_name=file_name, dir_path=dir_path)

    def download_validatiefouten(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self.rest_client.download_validatiefouten(aanlevering_id=aanlevering_id, file_name=file_name, dir_path=dir_path)

    def download_verificatierapport(self, aanlevering_id: str, file_name: str, dir_path: Path) -> None:
        self.rest_client.download_verificatierapport(aanlevering_id=aanlevering_id, file_name=file_name, dir_path=dir_path)

    def get_losse_validatie(self, id: str) -> LosseValidatie:
        return self.rest_client.get_losse_validatie(id=id)

    def list_losse_validatie_bestanden(self, id: str, from_: int = 0, size: int = 100) -> list[LosseValidatieBestandResultaat]:
        return self.rest_client.list_losse_validatie_bestanden(id=id, from_=from_, size=size)

