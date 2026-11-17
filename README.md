## Clone o repositório

```bash
git clone https://github.com/FernandoTinno/AtividadeBackend-4.git
```

**Mude para a pasta do projeto**

```bash
cd AtividadeBackend-4
```

**Acesse o diretório**

```bash
code . -r
```

**Crie um ambiente virtual**

```bash
py -m venv venv
```

**Acesse o ambiente virtual**

```bash
venv\Scripts\Activate.ps1
```

**Instale as dependências necessárias**

```bash
pip install -r requirements.txt
```

**Crie o Banco de dados**

```bash
alembic upgrade head
```

**Execute a aplicação**

```bash
py -m uvicorn main:app --reload
```

**Abra o link no navegador**

```bash
http://127.0.0.1:8000/docs
```

**Exemplo de Token**

```bash
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBlbWFpbC5jb20iLCJleHAiOjE3OTQzMzE5OTF9.WnQQE_a5kIUgX9Qj4iLmVtP2cIzB2rbiMpNT4gHVj9c",
  "token_type": "bearer"
}
```

**Execute os Testes Automatizados**

```bash
pytest -v
```