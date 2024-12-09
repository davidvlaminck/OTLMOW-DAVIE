from abc import ABC
from typing import Optional

from pydantic import Field, conlist
from pydantic import BaseModel as PydanticBaseModel

from otlmow_davie.Enums import AanleveringStatus, AanleveringSubstatus, MethodEnum, ExportType, LevelOfGeometry


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True


class OpgelijsteAanlevering(BaseModel):
    id: str
    isStudie: bool
    aanleveringnummer: str
    aanvrager: str
    referentie: str


# ondernemingInfo*	Onderneming{...}
    dossierNummer: str

    besteknummer: str

    dienstbevelnummer: str
# Het dienstbevelnummer van de aanlevering
# aanmaakDatum*	string($date-time)
# De datum waarop de aanlevering aangemaakt werd
# vervalOfEinddatum*	string($date)
# De vervaldatum van de aanlevering (indien de aanlevering nog niet in een eindstatus zit), of de einddatum (indien de aanlevering in een eindstatus zit)
# status*	string
# Status van de aanlevering
# Enum:
# Array [ 5 ]
# substatus	string
# Substatus van de aanlevering
# Enum:
# Array [ 6 ]
# omschrijving	string
# example: Het bestand werd opgeladen
# Een omschrijving van de laatste status wijziging
# type*	string
# Het type van de aanlevering
# Enum:
# Array [ 3 ]


class OpgelijsteAanleveringResultaat:
    aanlevering: OpgelijsteAanlevering


class PagedOpgelijsteAanleveringResultaat(BaseModel):
    data: list[OpgelijsteAanleveringResultaat]
    #links: PagedLinks
    from_: int = Field(..., alias='from')
    total: int
    size: int


class Aanlevering(BaseModel):
    """Groepeert alle informatie van een aanlevering"""
    id: str
    nummer: str
    status: AanleveringStatus
    substatus: Optional[AanleveringSubstatus]


class HateoasLink(BaseModel):
    href: str
    method: MethodEnum


class AanleveringHateoasLinks(BaseModel):
    """de HATEOAS links die van toepassing zijn op een aanlevering. Deze links geven aan welke acties mogelijk zijn
    op de aanlevering. Als een link ontbreekt op een aanlevering dan betekent dit dat de corresponderende actie niet
    mogelijk is op de aanlevering. """
    doorstromingfouten: Optional[HateoasLink]
    doorstromingidmapping: Optional[HateoasLink]
    doorstromingstatistieken: Optional[HateoasLink]
    exportaanvraag: Optional[HateoasLink]
    exportaanvraagfouten: Optional[HateoasLink]
    finaliseren: Optional[HateoasLink]
    genegeerdedata: Optional[HateoasLink]
    self: HateoasLink
    validatiefouten: Optional[HateoasLink]
    verificatierapport: Optional[HateoasLink]


class AanleveringResultaat(BaseModel):
    """Een aanlevering met zijn links. Deze links geven aan welke acties mogelijk zijn op de aanlevering. Als een
    link ontbreekt op een aanlevering dan betekent dit dat de corresponderende actie niet mogelijk is op de
    aanlevering. """
    aanlevering: Aanlevering
    links: AanleveringHateoasLinks

    class Config:
        use_enum_values = True


class AanleveringCreatie(BaseModel, ABC):
    pass


class AanleveringCreatieMedewerker(AanleveringCreatie):
    """Capteert alle informatie rond het aanmaken van een aanlevering voor AWV medewerker via een rechtstreekse (B2B)
    integratie met de davie-core REST API. """
    verificatorId: str
    besteknummer: Optional[str]
    bestekomschrijving: Optional[str]
    dienstbevelnummer: Optional[str]
    dienstbevelomschrijving: Optional[str]
    dossiernummer: Optional[str]
    referentie: str = Field(..., max_length=80)
    nota: Optional[str] = Field(None, max_length=250)
    type: str = 'aanmakenAanleveringMedewerker'
    niveau: str = None


class AanleveringCreatieOpdrachtnemer(AanleveringCreatie):
    """Capteert alle informatie rond het aanmaken van een aanlevering voor een opdrachtnemer via een rechtstreekse
    (B2B) integratie met de davie-core REST API. """
    ondernemingsnummer: str
    besteknummer: str
    dienstbevelnummer: Optional[str]
    dossiernummer: str
    referentie: str = Field(..., max_length=80)
    nota: Optional[str] = Field(None, max_length=250)
    type: str = 'aanmakenAanleveringOpdrachtnemer'


class AanleveringCreatieControlefiche(AanleveringCreatie):
    """Capteert alle informatie rond het aanmaken van een aanlevering voor een of meerdere controlefiches via een
    rechtstreekse (B2B) integratie met de davie-core REST API."""
    ondernemingsnummer: Optional[str]
    besteknummer: Optional[str]
    dienstbevelnummer: Optional[str]
    dossiernummer: Optional[str]
    referentie: Optional[str] = Field(..., max_length=80)
    type: str = 'aanmakenAanleveringControleFiche'


class AanleveringBestand(BaseModel):
    """Groepeert alle informatie van een bestand"""
    id: str
    aanleveringId: str


class AanleveringBestandHateoasLinks(BaseModel):
    """de HATEOAS links die van toepassing zijn op een bestand. Deze links geven aan welke acties mogelijk zijn op
    het bestand. Als een link ontbreekt op een bestand dan betekent dit dat de corresponderende actie niet mogelijk
    is op het bestand. """
    self: HateoasLink


class AanleveringBestandResultaat(BaseModel):
    """
    Een bestand met zijn links. Deze links geven aan welke acties mogelijk zijn op het bestand. Als een link
    ontbreekt op een bestand dan betekent dit dat de corresponderende actie niet mogelijk is op het bestand. """
    bestand: AanleveringBestand
    links: AanleveringBestandHateoasLinks


class AsIsAanvraagCreatie(BaseModel):
    """Capteert alle informatie rond het aanmaken van een asis aanvraag voor een aanlevering."""
    geometrie: Optional[str]
    exportType: ExportType
    assetTypes: list[str]
    levelOfGeometry: LevelOfGeometry = LevelOfGeometry.ALLES
    emailAdres: Optional[str]


class AsIsAanvraagHateoasLinks(BaseModel):
    """De HATEOAS links die van toepassing zijn op een asis aanvraag."""
    self: Optional[HateoasLink]


class AsIsAanvraag(BaseModel):
    """Groepeert alle informatie van een asis aanvraag van een aanlevering"""
    id: str
    aanleveringId: str


class AsIsAanvraagResultaat(BaseModel):
    """Een aanlevering met zijn links. Deze links geven aan welke acties mogelijk zijn op de aanlevering. Als een
    link ontbreekt op een aanlevering dan betekent dit dat de corresponderende actie niet mogelijk is op de
    aanlevering. """
    asisAanvraag: AsIsAanvraag
    links: Optional[AsIsAanvraagHateoasLinks]
