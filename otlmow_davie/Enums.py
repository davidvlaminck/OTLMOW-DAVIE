import enum


class Environment(enum.Enum):
    prd = 1
    tei = 2
    dev = 3


class AuthenticationType(enum.Enum):
    JWT = 1
    cert = 2


class AanleveringStatus(enum.Enum):
    GEANNULEERD = 1
    VERVALLEN = 2
    DATA_AANGELEVERD = 3
    DATA_AANGEVRAAGD = 4
    IN_OPMAAK = 5


class AanleveringSubstatus(enum.Enum):
    LOPEND = 1
    GEFAALD = 2
    BESCHIKBAAR = 3
    AANGEBODEN = 4
    GOEDGEKEURD = 5
    AFGEKEURD = 6
    OPGESCHORT = 7
