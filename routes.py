from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db

router = APIRouter()



@router.post(
    "/users/",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Autenticação & Usuários"],
    summary="Cadastrar novo usuário",
    response_description="Dados do usuário cadastrado (sem a senha)",
    responses={
        400: {"description": "E-mail já cadastrado no sistema"},
    },
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova conta de usuário no banco de dados:

    - **email**: E-mail válido e único do usuário.
    - **password**: Senha em texto plano (será armazenada com hash seguro **bcrypt**).
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já registrado")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post(
    "/token",
    response_model=schemas.Token,
    tags=["Autenticação & Usuários"],
    summary="Autenticar usuário (Gerar Token JWT)",
    response_description="Token de acesso JWT do tipo Bearer",
    responses={
        401: {"description": "E-mail ou senha inválidos"},
    },
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Valida as credenciais do usuário via formulário OAuth2 e retorna um **JWT**:

    - **username**: Informe o **e-mail** cadastrado do usuário.
    - **password**: Informe a **senha** correspondente.
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/tasks/",
    response_model=schemas.TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tarefas"],
    summary="Criar uma nova tarefa",
    response_description="Tarefa criada com seu respectivo ID",
    responses={
        401: {"description": "Token ausente, inválido ou expirado"},
    },
)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Registra uma nova tarefa no banco de dados (**Requer autenticação**):

    - **title**: Título obrigatório da tarefa.
    - **description**: Descrição detalhada opcional.
    - **completed**: Status de conclusão (padrão `false`).
    """
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get(
    "/tasks/",
    response_model=list[schemas.TaskResponse],
    tags=["Tarefas"],
    summary="Listar todas as tarefas",
    response_description="Lista paginada de tarefas cadastradas",
)
def read_tasks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Retorna a lista de tarefas cadastradas (**Rota pública**):

    - **skip**: Quantidade de registros a pular (paginação).
    - **limit**: Quantidade máxima de registros retornados por página.
    """
    return db.query(models.Task).offset(skip).limit(limit).all()


@router.get(
    "/tasks/{task_id}",
    response_model=schemas.TaskResponse,
    tags=["Tarefas"],
    summary="Buscar tarefa por ID",
    response_description="Detalhes da tarefa encontrada",
    responses={
        404: {"description": "Tarefa não encontrada"},
    },
)
def read_task(task_id: int, db: Session = Depends(get_db)):
    """
    Consulta uma tarefa específica pelo seu identificador único (**Rota pública**):

    - **task_id**: ID inteiro da tarefa desejada.
    """
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return task


@router.put(
    "/tasks/{task_id}",
    response_model=schemas.TaskResponse,
    tags=["Tarefas"],
    summary="Atualizar tarefa existente",
    response_description="Dados atualizados da tarefa",
    responses={
        401: {"description": "Token ausente, inválido ou expirado"},
        404: {"description": "Tarefa não encontrada"},
    },
)
def update_task(
    task_id: int,
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Atualiza todos os campos de uma tarefa existente (**Requer autenticação**):

    - **task_id**: ID inteiro da tarefa a ser atualizada.
    - **task**: Novos valores para `title`, `description` e `completed`.
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    for key, value in task.model_dump().items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete(
    "/tasks/{task_id}",
    tags=["Tarefas"],
    summary="Excluir uma tarefa",
    response_description="Confirmação de exclusão da tarefa",
    responses={
        401: {"description": "Token ausente, inválido ou expirado"},
        404: {"description": "Tarefa não encontrada"},
    },
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Remove permanentemente uma tarefa do banco de dados (**Requer autenticação**):

    - **task_id**: ID inteiro da tarefa que será excluída.
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    db.delete(db_task)
    db.commit()
    return {"message": "Tarefa excluída com sucesso"}