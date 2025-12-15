from fastapi import FastAPI
from app.routes.turnos import router as router_turnos

app = FastAPI(
    title="API de Turnos Hospitalarios",
    version="1.0.0",
    description="API para la gestión de turnos en un hospital.",
)

app.include_router(router_turnos, prefix="/api", tags=["Turnos"])

@app.get("/")
def raiz():
    return {"mensaje": "API de Turnos Hospitalarios funcionando ✅"}
