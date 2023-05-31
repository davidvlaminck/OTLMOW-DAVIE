from enum import Enum


class Environment(Enum):
    prd = 1
    tei = 2
    dev = 3
    aim = 4


class AuthenticationType(Enum):
    JWT = 1
    cert = 2


class AanleveringStatus(str, Enum):
    """De status van de aanlevering. De status is altijd aanwezig."""
    GEANNULEERD = 'GEANNULEERD'
    VERVALLEN = 'VERVALLEN'
    DATA_AANGELEVERD = 'DATA_AANGELEVERD'
    DATA_AANGEVRAAGD = 'DATA_AANGEVRAAGD'
    IN_OPMAAK = 'IN_OPMAAK'


class AanleveringSubstatus(str, Enum):
    """De substatus van de aanlevering. De substatus is optioneel."""
    LOPEND = 'LOPEND'
    GEFAALD = 'GEFAALD'
    BESCHIKBAAR = 'BESCHIKBAAR'
    AANGEBODEN = 'AANGEBODEN'
    GOEDGEKEURD = 'GOEDGEKEURD'
    AFGEKEURD = 'AFGEKEURD'
    OPGESCHORT = 'OPGESCHORT'


class ExportType(str, Enum):
    """De verschillende export formaten voor het aanvragen van een asis toestand."""
    JSON = 'json'
    CSV = 'csv'
    XLSX = 'xlsx'
    SDF = 'sdf'
    GEOJSON = 'geojson'


class LevelOfGeometry(str, Enum):
    """De verschillende export formaten voor het aanvragen van een asis toestand."""
    LOG0 = 'LOG0'
    LOGMIN1 = 'LOG-1'
    ALLES = 'Alles'
    ONGEKEND = 'Ongekend'


class MethodEnum(str, Enum):
    """De verschillende HTTP method verbs die worden ondersteund in een HATEOAS link"""
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
