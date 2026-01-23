# update_user_phone.py
"""
Script para atualizar telefone dos usuários no banco de dados.
Telefones são usados para enviar notificações via WhatsApp.

Formato do telefone: DDI + DDD + Número (sem espaços)
Exemplo: 5547999999999 (Brasil: 55, DDD: 47, Número: 999999999)
"""

from database import SessionLocal
from models import User


def atualizar_telefone(email: str, telefone: str):
    """Atualiza telefone de um usuário pelo email."""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ Usuário com email '{email}' não encontrado")
            return False
        
        user.telefone = telefone
        db.commit()
        
        print(f"✅ Telefone atualizado para {user.nome}: {telefone}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar telefone: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def listar_usuarios():
    """Lista todos os usuários e seus telefones."""
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        print("\n" + "="*60)
        print("USUÁRIOS CADASTRADOS")
        print("="*60)
        
        for user in users:
            telefone = user.telefone or "Não cadastrado"
            print(f"\n👤 {user.nome}")
            print(f"   Email: {user.email}")
            print(f"   Telefone: {telefone}")
            print(f"   Role: {user.role.value}")
        
        print("\n" + "="*60)
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    print("🔧 Gerenciador de Telefones - FluxoLand\n")
    
    # Se passou argumentos na linha de comando
    if len(sys.argv) == 3:
        email = sys.argv[1]
        telefone = sys.argv[2]
        atualizar_telefone(email, telefone)
    else:
        # Modo interativo
        listar_usuarios()
        
        print("\n" + "-"*60)
        print("Digite o email do usuário (ou Enter para sair):")
        email = input("Email: ").strip()
        
        if not email:
            print("Saindo...")
            sys.exit(0)
        
        print("\nDigite o telefone (formato: 5547999999999):")
        telefone = input("Telefone: ").strip()
        
        if telefone:
            atualizar_telefone(email, telefone)
        else:
            print("❌ Telefone não pode ser vazio")
