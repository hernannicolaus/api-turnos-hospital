from fastapi import FastAPI
from app.routes.turnos import router as router_turnos
from app.db import crear_bd_y_tablas

app = FastAPI(
    title="API de Turnos Hospitalarios",
    version="1.0.0",
    description="API para la gestión de turnos en un hospital (SQLite).",
)

@app.on_event("startup")
def on_startup():
    crear_bd_y_tablas()

app.include_router(router_turnos, prefix="/api", tags=["Turnos"])

@app.get("/")
def raiz():
    return {"mensaje": "API de Turnos Hospitalarios funcionando ✅"}
