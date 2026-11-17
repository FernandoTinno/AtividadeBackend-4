from fastapi import FastAPI
from routes import router

tags_metadata = [
    {
        "name": "Autenticação & Usuários",
        "description": "Operações para cadastro de novos usuários e geração de tokens de acesso **JWT (OAuth2)**.",
    },
    {
        "name": "Tarefas",
        "description": "Gerenciamento completo (CRUD) de tarefas. Rotas de leitura (**GET**) são públicas; rotas de escrita (**POST**, **PUT**, **DELETE**) exigem autenticação via Bearer Token.",
    },
]

app = FastAPI(
    title="API de Gerenciamento de Tarefas",
    description=(
        "API RESTful desenvolvida com **FastAPI**, **SQLAlchemy** e **SQLite**, "
        "protegida por autenticação **OAuth2 com JWT**.\n\n"
        "### Como autenticar:\n"
        "1. Crie uma conta em `POST /users/`.\n"
        "2. Clique no botão **Authorize** no topo da página e informe seu e-mail e senha."
    ),
    version="3.0.0",
    openapi_tags=tags_metadata,
)

app.include_router(router)