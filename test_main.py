import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone

from database import Base, get_db
from main import app

# Configura um banco SQLite em memória isolado exclusivo para os testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Sobrescreve a dependência do banco de dados na aplicação
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Cria as tabelas antes de cada teste e as destrói ao finalizar."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def get_auth_headers(email: str = "teste@email.com", password: str = "123456") -> dict:
    """Função auxiliar para registrar um usuário, fazer login e retornar o header Bearer."""
    client.post("/users/", json={"email": email, "password": password})
    response = client.post("/token", data={"username": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Teste de rota pública GET retornando 200
def test_read_tasks_public_returns_200():
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []


# 2. Teste de bloqueio 401 ao tentar criar tarefa sem token
def test_create_task_without_token_returns_401():
    response = client.post(
        "/tasks/",
        json={"title": "Tarefa não autorizada", "description": "Sem token", "completed": False},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# 3. Teste de criação de usuário e login gerando token JWT
def test_create_user_and_login_jwt():
    user_res = client.post(
        "/users/",
        json={"email": "aluno@ifms.edu.br", "password": "senhasegura"},
    )
    assert user_res.status_code == 201
    assert user_res.json()["email"] == "aluno@ifms.edu.br"
    assert "id" in user_res.json()

    login_res = client.post(
        "/token",
        data={"username": "aluno@ifms.edu.br", "password": "senhasegura"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# 4. Teste de criação (POST) e busca por ID (GET) com usuário autenticado
def test_create_and_read_task_authenticated():
    headers = get_auth_headers()

    create_res = client.post(
        "/tasks/",
        json={"title": "Estudar Pytest", "description": "Escrever testes com TestClient", "completed": False},
        headers=headers,
    )
    assert create_res.status_code == 201
    created_task = create_res.json()
    assert created_task["title"] == "Estudar Pytest"
    task_id = created_task["id"]

    # Verifica se a rota pública GET /{task_id} retorna a tarefa criada
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id
    assert get_res.json()["description"] == "Escrever testes com TestClient"


# 5. Teste de erro 404 ao buscar tarefa inexistente
def test_read_nonexistent_task_returns_404():
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa não encontrada"


# 6. Teste de atualização (PUT) protegida e funcional
def test_update_task_authenticated():
    headers = get_auth_headers()
    create_res = client.post(
        "/tasks/",
        json={"title": "Tarefa Inicial", "description": "Antes", "completed": False},
        headers=headers,
    )
    task_id = create_res.json()["id"]

    # Tentativa sem token deve falhar com 401
    unauth_res = client.put(
        f"/tasks/{task_id}",
        json={"title": "Hackeada", "description": "Sem token", "completed": True},
    )
    assert unauth_res.status_code == 401

    # Atualização com token deve retornar 200
    update_res = client.put(
        f"/tasks/{task_id}",
        json={"title": "Tarefa Concluída", "description": "Depois", "completed": True},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Tarefa Concluída"
    assert update_res.json()["completed"] is True


# 7. Teste de exclusão (DELETE) protegida e verificação de remoção
def test_delete_task_authenticated():
    headers = get_auth_headers()
    create_res = client.post(
        "/tasks/",
        json={"title": "Tarefa Temporária", "completed": False},
        headers=headers,
    )
    task_id = create_res.json()["id"]

    # Exclusão sem token deve falhar com 401
    unauth_del = client.delete(f"/tasks/{task_id}")
    assert unauth_del.status_code == 401

    # Exclusão com token deve retornar 200
    del_res = client.delete(f"/tasks/{task_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json() == {"message": "Tarefa excluída com sucesso"}

    # Confirmar que não existe mais no banco (404)
    confirm_res = client.get(f"/tasks/{task_id}")
    assert confirm_res.status_code == 404