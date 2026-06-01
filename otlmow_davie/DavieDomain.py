from abc import ABC
from typing import Optional, Union

from pydantic import AliasChoices, ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel

from otlmow_davie.Enums import AanleveringStatus, AanleveringSubstatus, ExportType, LevelOfGeometry as LevelOfGeometryEnum, MethodEnum


class BaseModel(PydanticBaseModel):
    # The API evolves frequently; allow unknown fields so parsing remains resilient.
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow', populate_by_name=True)


class OpgelijsteAanlevering(BaseModel):
    id: str
    isStudie: Optional[bool] = None
    aanleveringnummer: Optional[str] = None
    aanvrager: Optional[str] = None
    referentie: Optional[str] = None
    dossierNummer: Optional[str] = None
    besteknummer: Optional[str] = None
    dienstbevelnummer: Optional[str] = None
    aanmaakDatum: Optional[str] = None
    vervalOfEinddatum: Optional[str] = None
    status: Optional[AanleveringStatus] = None
    substatus: Optional[AanleveringSubstatus] = None
    omschrijving: Optional[str] = None
    type: Optional[str] = None


class OpgelijsteAanleveringResultaat(BaseModel):
    aanlevering: OpgelijsteAanlevering


class PagedOpgelijsteAanleveringResultaat(BaseModel):
    data: list[OpgelijsteAanleveringResultaat]
    from_: int = Field(..., alias='from')
    total: int
    size: int
    links: dict[str, object] = Field(default_factory=dict)


class ApiError(BaseModel):
    message: str
    detail: Optional[str] = None


class OndernemingInfo(BaseModel):
    ondernemingsnummer: Optional[str] = None
    naam: Optional[str] = None


class AanleveringInfo(BaseModel):
    dossiernummer: Optional[str] = None
    besteknummer: Optional[str] = None
    bestekOmschrijving: Optional[str] = None
    dienstbevelId: Optional[str] = None
    dienstbevelOmschrijving: Optional[str] = None
    ondernemingInfo: Optional[OndernemingInfo] = None


class Aanlevering(BaseModel):
    id: str
    nummer: Optional[str] = Field(default=None, validation_alias=AliasChoices('nummer', 'aanleveringnummer'))
    status: Optional[AanleveringStatus] = None
    substatus: Optional[AanleveringSubstatus] = None
    aanvrager: Optional[dict[str, object]] = None
    ondernemingsnummer: Optional[str] = None
    info: Optional[AanleveringInfo] = None
    vervalOfEinddatum: Optional[str] = None
    aangemaaktOp: Optional[str] = None
    aangemaaktDoor: Optional[dict[str, object]] = None
    gewijzigdOp: Optional[str] = None
    gewijzigdDoor: Optional[dict[str, object]] = None
    type: Optional[str] = None
    oorsprong: Optional[str] = None
    version: Optional[str] = None


class HateoasLink(BaseModel):
    href: str
    method: MethodEnum


class AanleveringHateoasLinks(BaseModel):
    bijlageopladen: Optional[HateoasLink] = None
    hoofdbestandopladen: Optional[HateoasLink] = None
    doorstromingfouten: Optional[HateoasLink] = None
    doorstromingidmapping: Optional[HateoasLink] = None
    doorstromingstatistieken: Optional[HateoasLink] = None
    exportaanvraag: Optional[HateoasLink] = None
    exportaanvraagfouten: Optional[HateoasLink] = None
    finaliseren: Optional[HateoasLink] = None
    genegeerdedata: Optional[HateoasLink] = None
    self: Optional[HateoasLink] = None
    validatiefouten: Optional[HateoasLink] = None
    verificatierapport: Optional[HateoasLink] = None


class AanleveringHistoriekItem(BaseModel):
    tijdstip: str
    volledigeNaam: str
    omschrijving: Optional[str] = None
    status: Optional[AanleveringStatus] = None
    substatus: Optional[AanleveringSubstatus] = None
    links: dict[str, object] = Field(default_factory=dict)


class PagedAanleveringHistoriekResultaat(BaseModel):
    data: list[AanleveringHistoriekItem]
    from_: int = Field(..., alias='from')
    total: int
    size: int
    links: dict[str, object] = Field(default_factory=dict)

class AanleveringResultaat(BaseModel):
    aanlevering: Aanlevering
    links: AanleveringHateoasLinks


class AanleveringCreatie(BaseModel, ABC):
    pass


class AanleveringCreatieMedewerker(AanleveringCreatie):
    verificatorId: str
    besteknummer: Optional[str] = None
    bestekomschrijving: Optional[str] = None
    dienstbevelnummer: Optional[str] = None
    dienstbevelomschrijving: Optional[str] = None
    dossiernummer: Optional[str] = None
    referentie: str = Field(..., max_length=80)
    nota: Optional[str] = Field(None, max_length=250)
    type: str = 'aanmakenAanleveringMedewerker'
    niveau: Optional[str] = None


class AanleveringCreatieOpdrachtnemer(AanleveringCreatie):
    ondernemingsnummer: str
    besteknummer: str
    dienstbevelnummer: Optional[str] = None
    dossiernummer: str
    referentie: str = Field(..., max_length=80)
    nota: Optional[str] = Field(None, max_length=250)
    type: str = 'aanmakenAanleveringOpdrachtnemer'


class AanleveringCreatieControlefiche(AanleveringCreatie):
    ondernemingsnummer: Optional[str] = None
    besteknummer: Optional[str] = None
    dienstbevelnummer: Optional[str] = None
    dossiernummer: Optional[str] = None
    referentie: Optional[str] = Field(..., max_length=80)
    type: str = 'aanmakenAanleveringControleFiche'


class AanleveringBestand(BaseModel):
    id: str
    aanleveringId: Optional[str] = None
    argusId: Optional[str] = None
    bestandsnaam: Optional[str] = None
    aangemaaktOp: Optional[str] = None
    aangemaaktDoor: Optional[dict[str, object]] = None
    grootte: Optional[str] = None
    bestandMetadata: dict[str, object] = Field(default_factory=dict)
    version: Optional[str] = None
    artefactId: Optional[str] = None


class AanleveringBestandHateoasLinks(BaseModel):
    self: Optional[HateoasLink] = None


class AanleveringBestandResultaat(BaseModel):
    bestand: AanleveringBestand
    links: AanleveringBestandHateoasLinks


class PagedAanleveringBestandResultaat(BaseModel):
    data: list[AanleveringBestandResultaat]
    from_: int = Field(..., alias='from')
    total: int
    size: int
    links: dict[str, object] = Field(default_factory=dict)


class AsIsAssetType(BaseModel):
    typeURI: str
    includeRelaties: Optional[bool] = None


class XlsxExportOptions(BaseModel):
    includeAfgeleideWeglocatie: Optional[bool] = None
    includePuntlocaties: Optional[bool] = None
    includeGeometrieInfo: Optional[bool] = None
    includeRelatieInfo: Optional[bool] = None


class AsIsAanvraagCreatie(BaseModel):
    geometrie: Optional[str] = None
    exportType: ExportType
    assetTypes: list[Union[str, AsIsAssetType]]
    levelOfGeometry: LevelOfGeometryEnum = LevelOfGeometryEnum.ALLES
    emailAdres: Optional[str] = None
    xlsxExportOptions: Optional[XlsxExportOptions] = None


class AsIsAanvraagHateoasLinks(BaseModel):
    self: Optional[HateoasLink]


class AsIsAanvraag(BaseModel):
    id: str
    aanleveringId: str
    exportType: Optional[ExportType] = None
    status: Optional[str] = None
    oorsprong: Optional[str] = None
    version: Optional[str] = None


class AsIsAanvraagResultaat(BaseModel):
    asisAanvraag: AsIsAanvraag
    links: dict[str, HateoasLink] = Field(default_factory=dict)


class PagedAsIsAanvraagResultaat(BaseModel):
    data: list[AsIsAanvraagResultaat]
    from_: int = Field(..., alias='from')
    total: int
    size: int
    links: dict[str, object] = Field(default_factory=dict)


class LosseValidatie(BaseModel):
    id: str
    nummer: Optional[str] = None
    status: Optional[str] = None
    substatus: Optional[str] = None
    type: Optional[str] = None
    oorsprong: Optional[str] = None
    version: Optional[str] = None
    links: dict[str, object] = Field(default_factory=dict)


class LosseValidatieResultaat(BaseModel):
    losseValidatie: LosseValidatie
    links: dict[str, object] = Field(default_factory=dict)


class LosseValidatieBestand(BaseModel):
    id: str
    argusId: Optional[str] = None
    bestandsnaam: Optional[str] = None
    aangemaaktOp: Optional[str] = None
    aangemaaktDoor: Optional[dict[str, object]] = None
    grootte: Optional[str] = None
    bestandMetadata: dict[str, object] = Field(default_factory=dict)
    version: Optional[str] = None
    artefactId: Optional[str] = None


class LosseValidatieBestandResultaat(BaseModel):
    bestand: LosseValidatieBestand
    links: dict[str, object] = Field(default_factory=dict)


class PagedLosseValidatieBestandResultaat(BaseModel):
    data: list[LosseValidatieBestandResultaat]
    from_: int = Field(..., alias='from')
    total: int
    size: int
    links: dict[str, object] = Field(default_factory=dict)

