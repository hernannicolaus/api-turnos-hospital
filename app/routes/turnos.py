from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.schemas import (
    Paciente, PacienteCrear,
    Profesional, ProfesionalCrear,
    Turno, TurnoCrear, EstadoTurno
)
from app.models.tablas import PacienteDB, ProfesionalDB, TurnoDB

router = APIRouter()


def _solapa(inicio_a: datetime, dur_a: int, inicio_b: datetime, dur_b: int) -> bool:
    fin_a = inicio_a + timedelta(minutes=dur_a)
    fin_b = inicio_b + timedelta(minutes=dur_b)
    return inicio_a < fin_b and inicio_b < fin_a


@router.get("/ping")
def ping():
    return {"mensaje": "pong ✅"}


# ----------------------------
# Pacientes
# ----------------------------
@router.post("/pacientes", response_model=Paciente, status_code=201)
def crear_paciente(data: PacienteCrear, session: Session = Depends(get_session)):
    paciente = PacienteDB(nombre=data.nombre, dni=data.dni)
    session.add(paciente)
    session.commit()
    session.refresh(paciente)
    return Paciente(id=paciente.id, nombre=paciente.nombre, dni=paciente.dni)


@router.get("/pacientes", response_model=List[Paciente])
def listar_pacientes(session: Session = Depends(get_session)):
    pacientes = session.exec(select(PacienteDB)).all()
    return [Paciente(id=p.id, nombre=p.nombre, dni=p.dni) for p in pacientes]


@router.get("/pacientes/{paciente_id}", response_model=Paciente)
def obtener_paciente(paciente_id: int, session: Session = Depends(get_session)):
    paciente = session.get(PacienteDB, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return Paciente(id=paciente.id, nombre=paciente.nombre, dni=paciente.dni)


# ----------------------------
# Profesionales
# ----------------------------
@router.post("/profesionales", response_model=Profesional, status_code=201)
def crear_profesional(data: ProfesionalCrear, session: Session = Depends(get_session)):
    profesional = ProfesionalDB(nombre=data.nombre, especialidad=data.especialidad)
    session.add(profesional)
    session.commit()
    session.refresh(profesional)
    return Profesional(id=profesional.id, nombre=profesional.nombre, especialidad=profesional.especialidad)


@router.get("/profesionales", response_model=List[Profesional])
def listar_profesionales(session: Session = Depends(get_session)):
    profesionales = session.exec(select(ProfesionalDB)).all()
    return [Profesional(id=p.id, nombre=p.nombre, especialidad=p.especialidad) for p in profesionales]


@router.get("/profesionales/{profesional_id}", response_model=Profesional)
def obtener_profesional(profesional_id: int, session: Session = Depends(get_session)):
    profesional = session.get(ProfesionalDB, profesional_id)
    if not profesional:
        raise HTTPException(status_code=404, detail="Profesional no encontrado")
    return Profesional(id=profesional.id, nombre=profesional.nombre, especialidad=profesional.especialidad)


# ----------------------------
# Turnos
# ----------------------------
@router.post("/turnos", response_model=Turno, status_code=201)
def crear_turno(data: TurnoCrear, session: Session = Depends(get_session)):
    # Validar existencia en SQLite
    paciente = session.get(PacienteDB, data.paciente_id)
    if not paciente:
        raise HTTPException(status_code=400, detail="Paciente inexistente")

    profesional = session.get(ProfesionalDB, data.profesional_id)
    if not profesional:
        raise HTTPException(status_code=400, detail="Profesional inexistente")

    # Validar solapamiento contra turnos RESERVADOS del profesional
    turnos_reservados = session.exec(
        select(TurnoDB).where(
            TurnoDB.profesional_id == data.profesional_id,
            TurnoDB.estado == EstadoTurno.reservado.value,
        )
    ).all()

    for t in turnos_reservados:
        if _solapa(t.inicio, t.duracion_minutos, data.inicio, data.duracion_minutos):
            raise HTTPException(
                status_code=400,
                detail="Turno solapado: el profesional ya tiene un turno en ese horario",
            )

    turno_db = TurnoDB(
        paciente_id=data.paciente_id,
        profesional_id=data.profesional_id,
        inicio=data.inicio,
        duracion_minutos=data.duracion_minutos,
        estado=EstadoTurno.reservado.value,
    )
    session.add(turno_db)
    session.commit()
    session.refresh(turno_db)

    return Turno(
        id=turno_db.id,
        paciente_id=turno_db.paciente_id,
        profesional_id=turno_db.profesional_id,
        inicio=turno_db.inicio,
        duracion_minutos=turno_db.duracion_minutos,
        estado=EstadoTurno(turno_db.estado),
    )


@router.get("/turnos", response_model=List[Turno])
def listar_turnos(
    session: Session = Depends(get_session),
    desde: Optional[datetime] = Query(default=None),
    hasta: Optional[datetime] = Query(default=None),
    profesional_id: Optional[int] = Query(default=None),
    estado: Optional[EstadoTurno] = Query(default=None),
):
    stmt = select(TurnoDB)

    if desde is not None:
        stmt = stmt.where(TurnoDB.inicio >= desde)
    if hasta is not None:
        stmt = stmt.where(TurnoDB.inicio <= hasta)
    if profesional_id is not None:
        stmt = stmt.where(TurnoDB.profesional_id == profesional_id)
    if estado is not None:
        stmt = stmt.where(TurnoDB.estado == estado.value)

    turnos = session.exec(stmt).all()
    return [
        Turno(
            id=t.id,
            paciente_id=t.paciente_id,
            profesional_id=t.profesional_id,
            inicio=t.inicio,
            duracion_minutos=t.duracion_minutos,
            estado=EstadoTurno(t.estado),
        )
        for t in turnos
    ]


@router.patch("/turnos/{turno_id}/cancelar", response_model=Turno)
def cancelar_turno(turno_id: int, session: Session = Depends(get_session)):
    turno = session.get(TurnoDB, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno inexistente")

    if turno.estado != EstadoTurno.reservado.value:
        raise HTTPException(status_code=400, detail="Solo se puede cancelar un turno reservado")

    turno.estado = EstadoTurno.cancelado.value
    session.add(turno)
    session.commit()
    session.refresh(turno)

    return Turno(
        id=turno.id,
        paciente_id=turno.paciente_id,
        profesional_id=turno.profesional_id,
        inicio=turno.inicio,
        duracion_minutos=turno.duracion_minutos,
        estado=EstadoTurno(turno.estado),
    )


@router.patch("/turnos/{turno_id}/atender", response_model=Turno)
def atender_turno(turno_id: int, session: Session = Depends(get_session)):
    turno = session.get(TurnoDB, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno inexistente")

    if turno.estado != EstadoTurno.reservado.value:
        raise HTTPException(status_code=400, detail="Solo se puede atender un turno reservado")

    turno.estado = EstadoTurno.atendido.value
    session.add(turno)
    session.commit()
    session.refresh(turno)

    return Turno(
        id=turno.id,
        paciente_id=turno.paciente_id,
        profesional_id=turno.profesional_id,
        inicio=turno.inicio,
        duracion_minutos=turno.duracion_minutos,
        estado=EstadoTurno(turno.estado),
    )
