import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_session


# SQLite en memoria, persistiendo dentro del mismo proceso de test
engine_test = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def get_session_test():
    with Session(engine_test) as session:
        yield session

@pytest.fixture(scope="function")
def client():
    # Reset total por test
    SQLModel.metadata.drop_all(engine_test)
    SQLModel.metadata.create_all(engine_test)

    # Override de la sesión real por la de test
    app.dependency_overrides[get_session] = get_session_test

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
