from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.services.store import store

client = TestClient(app)


def _resetear_store():
    # Reseteo completo del store en memoria para que los tests sean independientes
    store._pacientes.clear()
    store._profesionales.clear()
    store._turnos.clear()
    store._next_paciente_id = 1
    store._next_profesional_id = 1
    store._next_turno_id = 1


def _crear_paciente():
    r = client.post("/api/pacientes", json={"nombre": "Juan Perez", "dni": "30123456"})
    assert r.status_code == 201
    return r.json()["id"]


def _crear_profesional():
    r = client.post("/api/profesionales", json={"nombre": "Dra. Gomez", "especialidad": "Clinica"})
    assert r.status_code == 201
    return r.json()["id"]


def test_ping():
    _resetear_store()
    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.json()["mensaje"] == "pong ✅"


def test_crear_y_listar_turnos():
    _resetear_store()
    paciente_id = _crear_paciente()
    profesional_id = _crear_profesional()

    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2025-12-15T14:30:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201
    turno = r.json()
    assert turno["estado"] == "reservado"

    r = client.get("/api/turnos")
    assert r.status_code == 200
    turnos = r.json()
    assert len(turnos) == 1


def test_no_permite_turnos_solapados_para_mismo_profesional():
    _resetear_store()
    paciente_id = _crear_paciente()
    profesional_id = _crear_profesional()

    r1 = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2025-12-15T14:30:00",
        "duracion_minutos": 30
    })
    assert r1.status_code == 201

    r2 = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2025-12-15T14:45:00",
        "duracion_minutos": 30
    })
    assert r2.status_code == 400
    assert "Turno solapado" in r2.json()["detail"]


def test_filtro_por_profesional():
    _resetear_store()
    paciente_id = _crear_paciente()

    prof_1 = _crear_profesional()
    r = client.post("/api/profesionales", json={"nombre": "Dr. Lopez", "especialidad": "Pediatria"})
    assert r.status_code == 201
    prof_2 = r.json()["id"]

    # Turno para prof_1
    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": prof_1,
        "inicio": "2025-12-15T10:00:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201

    # Turno para prof_2 (no solapa porque es otro profesional)
    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": prof_2,
        "inicio": "2025-12-15T10:00:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201

    r = client.get(f"/api/turnos?profesional_id={prof_1}")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["profesional_id"] == prof_1


def test_filtro_por_estado():
    _resetear_store()
    paciente_id = _crear_paciente()
    profesional_id = _crear_profesional()

    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2025-12-15T14:30:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201
    turno_id = r.json()["id"]

    # Cancelar
    r = client.patch(f"/api/turnos/{turno_id}/cancelar")
    assert r.status_code == 200
    assert r.json()["estado"] == "cancelado"

    # Filtrar cancelados
    r = client.get("/api/turnos?estado=cancelado")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["estado"] == "cancelado"


def test_filtro_por_fecha_desde_hasta():
    _resetear_store()
    paciente_id = _crear_paciente()
    profesional_id = _crear_profesional()

    # Dentro del rango
    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2025-12-10T09:00:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201

    # Fuera del rango (enero)
    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2026-01-05T09:00:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201

    desde = "2025-12-01T00:00:00"
    hasta = "2025-12-31T23:59:59"

    r = client.get(f"/api/turnos?desde={desde}&hasta={hasta}")
    assert r.status_code == 200
    turnos = r.json()
    assert len(turnos) == 1
    assert datetime.fromisoformat(turnos[0]["inicio"]) >= datetime.fromisoformat(desde)
    assert datetime.fromisoformat(turnos[0]["inicio"]) <= datetime.fromisoformat(hasta)
