from datetime import datetime, timedelta
from typing import Optional, List

from app.models.schemas import (
    Paciente, PacienteCrear,
    Profesional, ProfesionalCrear,
    Turno, TurnoCrear, EstadoTurno
)


class Store:
    def __init__(self):
        self._pacientes: list[Paciente] = []
        self._profesionales: list[Profesional] = []
        self._turnos: list[Turno] = []

        self._next_paciente_id = 1
        self._next_profesional_id = 1
        self._next_turno_id = 1

    # ---- Pacientes ----
    def crear_paciente(self, data: PacienteCrear) -> Paciente:
        paciente = Paciente(id=self._next_paciente_id, **data.model_dump())
        self._next_paciente_id += 1
        self._pacientes.append(paciente)
        return paciente

    def obtener_paciente(self, paciente_id: int) -> Optional[Paciente]:
        return next((p for p in self._pacientes if p.id == paciente_id), None)

    # ---- Profesionales ----
    def crear_profesional(self, data: ProfesionalCrear) -> Profesional:
        profesional = Profesional(id=self._next_profesional_id, **data.model_dump())
        self._next_profesional_id += 1
        self._profesionales.append(profesional)
        return profesional

    def obtener_profesional(self, profesional_id: int) -> Optional[Profesional]:
        return next((p for p in self._profesionales if p.id == profesional_id), None)

    # ---- Turnos ----
    def _solapa(self, inicio_a: datetime, dur_a: int, inicio_b: datetime, dur_b: int) -> bool:
        fin_a = inicio_a + timedelta(minutes=dur_a)
        fin_b = inicio_b + timedelta(minutes=dur_b)
        return inicio_a < fin_b and inicio_b < fin_a

    def crear_turno(self, data: TurnoCrear) -> Turno:
        if not self.obtener_paciente(data.paciente_id):
            raise ValueError("Paciente inexistente")
        if not self.obtener_profesional(data.profesional_id):
            raise ValueError("Profesional inexistente")

        for t in self._turnos:
            if t.profesional_id == data.profesional_id and t.estado == EstadoTurno.reservado:
                if self._solapa(t.inicio, t.duracion_minutos, data.inicio, data.duracion_minutos):
                    raise ValueError("Turno solapado: el profesional ya tiene un turno en ese horario")

        turno = Turno(
            id=self._next_turno_id,
            paciente_id=data.paciente_id,
            profesional_id=data.profesional_id,
            inicio=data.inicio,
            duracion_minutos=data.duracion_minutos,
            estado=EstadoTurno.reservado,
        )
        self._next_turno_id += 1
        self._turnos.append(turno)
        return turno

    def listar_turnos(
        self,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        profesional_id: Optional[int] = None,
        estado: Optional[EstadoTurno] = None,
    ) -> List[Turno]:
        # Filtra por fecha de inicio
        resultados = self._turnos
        if desde:
            resultados = [t for t in resultados if t.inicio >= desde]
        if hasta:
            resultados = [t for t in resultados if t.inicio <= hasta]
        
        # Filtra por ID de profesional
        if profesional_id:
            resultados = [t for t in resultados if t.profesional_id == profesional_id]

        # Filtra por estado
        if estado:
            resultados = [t for t in resultados if t.estado == estado]

        return resultados


    def cancelar_turno(self, turno_id: int) -> Turno:
        turno = next((t for t in self._turnos if t.id == turno_id), None)
        if not turno:
            raise ValueError("Turno inexistente")
        if turno.estado != EstadoTurno.reservado:
            raise ValueError("Solo se puede cancelar un turno reservado")
        turno.estado = EstadoTurno.cancelado
        return turno

    def atender_turno(self, turno_id: int) -> Turno:
        turno = next((t for t in self._turnos if t.id == turno_id), None)
        if not turno:
            raise ValueError("Turno inexistente")
        if turno.estado != EstadoTurno.reservado:
            raise ValueError("Solo se puede atender un turno reservado")
        turno.estado = EstadoTurno.atendido
        return turno


store = Store()
