# create_admin.py
from getpass import getpass
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import SessionLocal
from models import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_admin(nome: str, email: str, senha: str):
    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            print(f"Usuário {email} já existe. Atualizando para líder.")
            existing.nome = nome
            existing.senha_hash = hash_password(senha)
            existing.role = UserRole.lider
            existing.ativo = True
            db.commit()
            print("Usuário atualizado com sucesso.")
            return

        admin = User(
            nome=nome,
            email=email,
            senha_hash=hash_password(senha),
            role=UserRole.lider,
            ativo=True,
        )

        db.add(admin)
        db.commit()
        print("Usuário líder criado com sucesso.")


if __name__ == "__main__":
    nome = input("Nome do admin: ").strip()
    email = input("Email do admin: ").strip()
    senha = getpass("Senha do admin (não será exibida): ").strip()

    if not nome or not email or not senha:
        print("Nome, email e senha são obrigatórios.")
    else:
        create_admin(nome, email, senha)
