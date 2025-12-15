from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class PacienteDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    dni: str


class ProfesionalDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    especialidad: str


class TurnoDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paciente_id: int = Field(foreign_key="pacientedb.id")
    profesional_id: int = Field(foreign_key="profesionaldb.id")
    inicio: datetime
    duracion_minutos: int
    estado: str  # "reservado" | "cancelado" | "atendido"
