from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    Paciente, PacienteCrear,
    Profesional, ProfesionalCrear,
    Turno, TurnoCrear
)
from app.services.store import store

router = APIRouter()

@router.get("/ping")
def ping():
    return {"mensaje": "pong ✅"}

@router.post("/pacientes", response_model=Paciente, status_code=201)
def crear_paciente(data: PacienteCrear):
    return store.crear_paciente(data)

@router.post("/profesionales", response_model=Profesional, status_code=201)
def crear_profesional(data: ProfesionalCrear):
    return store.crear_profesional(data)

@router.post("/turnos", response_model=Turno, status_code=201)
def crear_turno(data: TurnoCrear):
    try:
        return store.crear_turno(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/turnos", response_model=list[Turno])
def listar_turnos():
    return store.listar_turnos()

@router.patch("/turnos/{turno_id}/cancelar", response_model=Turno)
def cancelar_turno(turno_id: int):
    try:
        return store.cancelar_turno(turno_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/turnos/{turno_id}/atender", response_model=Turno)
def atender_turno(turno_id: int):
    try:
        return store.atender_turno(turno_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
