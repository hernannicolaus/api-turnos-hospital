from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EstadoTurno(str, Enum):
    reservado = "reservado"
    cancelado = "cancelado"
    atendido = "atendido"


class PacienteCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    dni: str = Field(min_length=6, max_length=12)


class Paciente(PacienteCrear):
    id: int


class ProfesionalCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    especialidad: str = Field(min_length=2, max_length=80)


class Profesional(ProfesionalCrear):
    id: int


class TurnoCrear(BaseModel):
    paciente_id: int
    profesional_id: int
    inicio: datetime
    duracion_minutos: int = Field(gt=0, le=240)


class Turno(BaseModel):
    id: int
    paciente_id: int
    profesional_id: int
    inicio: datetime
    duracion_minutos: int
    estado: EstadoTurno
