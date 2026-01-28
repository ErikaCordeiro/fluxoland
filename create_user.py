from __future__ import annotations

from getpass import getpass

from database import SessionLocal
from models import User, UserRole


def _parse_role(raw: str) -> UserRole:
    value = (raw or "").strip().lower()
    if not value:
        return UserRole.usuario
    if value in ("usuario", "usuário", "user"):
        return UserRole.usuario
    if value in ("lider", "líder", "admin"):
        return UserRole.lider
    raise ValueError("Role inválida. Use 'usuario' ou 'lider'.")


def create_or_update_user(
    *,
    nome: str,
    email: str,
    senha: str,
    role: UserRole = UserRole.usuario,
    telefone: str | None = None,
) -> None:
    # Reutiliza o mesmo hashing usado na aplicação
    from auth import get_password_hash

    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.nome = nome
            existing.senha_hash = get_password_hash(senha)
            existing.role = role
            existing.ativo = True
            if telefone is not None:
                existing.telefone = telefone.strip() or None
            db.commit()
            print("Usuário atualizado com sucesso.")
            return

        user = User(
            nome=nome,
            email=email,
            senha_hash=get_password_hash(senha),
            role=role,
            ativo=True,
            telefone=(telefone.strip() or None) if telefone is not None else None,
        )

        db.add(user)
        db.commit()
        print("Usuário criado com sucesso.")


if __name__ == "__main__":
    nome = input("Nome: ").strip()
    email = input("Email: ").strip()
    telefone = input("Telefone (opcional, ex: 5547999999999): ").strip()
    senha = getpass("Senha (não será exibida): ").strip()

    if not nome or not email or not senha:
        print("Nome, email e senha são obrigatórios.")
        raise SystemExit(1)

    while True:
        role_raw = input("Role (usuario/lider) [usuario]: ").strip()
        try:
            role = _parse_role(role_raw)
            break
        except ValueError as exc:
            print(str(exc))

    create_or_update_user(
        nome=nome,
        email=email,
        senha=senha,
        role=role,
        telefone=telefone if telefone else None,
    )
