from enum import Enum


class Environment(Enum):
    prd = 1
    tei = 2
    dev = 3


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
