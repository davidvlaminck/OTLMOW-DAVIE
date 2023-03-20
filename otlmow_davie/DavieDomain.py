from pydantic import BaseModel

from otlmow_davie.Enums import AanleveringStatus, AanleveringSubstatus


class Aanlevering(BaseModel):
    """Groepeert alle informatie van een aanlevering"""
    id: str
    nummer: str
    status: AanleveringStatus
    substatus: AanleveringSubstatus
