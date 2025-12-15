def _crear_paciente(client):
    r = client.post("/api/pacientes", json={"nombre": "Juan Perez", "dni": "30123456"})
    assert r.status_code == 201
    return r.json()["id"]

def _crear_profesional(client, nombre="Dra. Gomez"):
    r = client.post("/api/profesionales", json={"nombre": nombre, "especialidad": "Clinica"})
    assert r.status_code == 201
    return r.json()["id"]

def test_ping(client):
    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.json()["mensaje"] == "pong ✅"

def test_crear_y_listar_turnos(client):
    paciente_id = _crear_paciente(client)
    profesional_id = _crear_profesional(client)

    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2025-12-15T14:30:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201
    assert r.json()["estado"] == "reservado"

    r = client.get("/api/turnos")
    assert r.status_code == 200
    turnos = r.json()

    # solo verificamos que exista al menos uno
    assert len(turnos) >= 1


def test_no_permite_turnos_solapados(client):
    paciente_id = _crear_paciente(client)
    profesional_id = _crear_profesional(client)

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

def test_filtros_por_profesional_y_estado(client):
    paciente_id = _crear_paciente(client)
    prof_1 = _crear_profesional(client, nombre="Dra. A")
    prof_2 = _crear_profesional(client, nombre="Dr. B")

    # turno prof_1
    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": prof_1,
        "inicio": "2025-12-10T10:00:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201
    turno_id = r.json()["id"]

    # turno prof_2
    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": prof_2,
        "inicio": "2025-12-10T11:00:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201

    # cancelar el turno de prof_1
    r = client.patch(f"/api/turnos/{turno_id}/cancelar")
    assert r.status_code == 200
    assert r.json()["estado"] == "cancelado"

    # filtro por profesional_id=prof_1 -> debería traer 1
    r = client.get(f"/api/turnos?profesional_id={prof_1}")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # filtro por estado=cancelado -> debería traer 1
    r = client.get("/api/turnos?estado=cancelado")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["estado"] == "cancelado"

def test_filtro_por_rango_de_fechas(client):
    paciente_id = _crear_paciente(client)
    profesional_id = _crear_profesional(client)

    # dentro del rango (diciembre)
    r = client.post("/api/turnos", json={
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "inicio": "2025-12-20T09:00:00",
        "duracion_minutos": 30
    })
    assert r.status_code == 201

    # fuera del rango (enero)
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
    assert len(turnos) >= 1

    for t in turnos:
        assert t["inicio"] >= desde
        assert t["inicio"] <= hasta

