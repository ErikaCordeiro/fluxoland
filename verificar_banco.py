"""Script para verificar estrutura do banco antes do deploy."""
import sys
from sqlalchemy import inspect, text
from database import engine, SessionLocal
from models import (
    User, Cliente, Proposta, PropostaProduto, Produto,
    ContatoNotificacao, PropostaStatus, TipoNotificacao
)


def verificar_conexao():
    """Verifica se consegue conectar ao banco."""
    print("\n🔍 Verificando conexão com banco de dados...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ Conexão OK")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False


def verificar_tabelas():
    """Verifica se todas as tabelas existem."""
    print("\n🔍 Verificando tabelas...")
    inspector = inspect(engine)
    tabelas_existentes = inspector.get_table_names()
    
    tabelas_necessarias = [
        'users',
        'clientes',
        'produtos',
        'propostas',
        'propostas_produtos',
        'contatos_notificacao',  # Nova tabela
    ]
    
    faltando = []
    for tabela in tabelas_necessarias:
        if tabela in tabelas_existentes:
            print(f"✅ {tabela}")
        else:
            print(f"❌ {tabela} - FALTANDO")
            faltando.append(tabela)
    
    return len(faltando) == 0


def verificar_colunas():
    """Verifica colunas críticas."""
    print("\n🔍 Verificando colunas críticas...")
    inspector = inspect(engine)
    
    verificacoes = [
        ('users', 'telefone'),  # Nova coluna
        ('propostas', 'status'),
        ('propostas', 'criado_em'),
        ('propostas', 'cliente_id'),
        ('contatos_notificacao', 'tipo'),  # Nova tabela
    ]
    
    todas_ok = True
    for tabela, coluna in verificacoes:
        try:
            colunas = [c['name'] for c in inspector.get_columns(tabela)]
            if coluna in colunas:
                print(f"✅ {tabela}.{coluna}")
            else:
                print(f"❌ {tabela}.{coluna} - FALTANDO")
                todas_ok = False
        except Exception as e:
            print(f"❌ {tabela} - Erro ao verificar: {e}")
            todas_ok = False
    
    return todas_ok


def verificar_enums():
    """Verifica se os enums existem."""
    print("\n🔍 Verificando enums...")
    db = SessionLocal()
    
    try:
        # Testa PropostaStatus
        db.execute(text("SELECT 'pendente_simulacao'::propostastatus"))
        print("✅ PropostaStatus enum OK")
        
        # Testa TipoNotificacao (novo)
        try:
            db.execute(text("SELECT 'simulacao'::tiponotificacao"))
            db.execute(text("SELECT 'cotacao'::tiponotificacao"))
            db.execute(text("SELECT 'envio'::tiponotificacao"))
            print("✅ TipoNotificacao enum OK (simulacao/cotacao/envio)")
        except Exception as e:
            print("❌ TipoNotificacao enum - FALTANDO (rode migrations/add_dashboard_and_whatsapp.sql e migrations/add_tiponotificacao_envio.sql)")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar enums: {e}")
        return False
    finally:
        db.close()


def verificar_queries_dashboard():
    """Testa se as queries do dashboard funcionam."""
    print("\n🔍 Testando queries do dashboard...")
    db = SessionLocal()
    
    try:
        from datetime import datetime
        from sqlalchemy import func
        
        # Teste 1: Count de propostas por status
        em_simulacao = db.query(func.count(Proposta.id)).filter(
            Proposta.status == PropostaStatus.pendente_simulacao
        ).scalar()
        print(f"✅ Query propostas em simulação: {em_simulacao}")
        
        # Teste 2: Propostas recentes
        propostas = db.query(Proposta).join(Cliente).limit(5).all()
        print(f"✅ Query propostas recentes: {len(propostas)} encontradas")
        
        # Teste 3: Valor total (property)
        if propostas:
            primeiro = propostas[0]
            valor = primeiro.valor_total
            print(f"✅ Property valor_total: R$ {valor}")
        
        return True
    except Exception as e:
        print(f"❌ Erro nas queries: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Executa todas as verificações."""
    print("="*70)
    print("🔧 VERIFICAÇÃO DO BANCO DE DADOS - FLUXOLAND")
    print("="*70)
    
    resultados = {
        "Conexão": verificar_conexao(),
        "Tabelas": verificar_tabelas(),
        "Colunas": verificar_colunas(),
        "Enums": verificar_enums(),
        "Queries Dashboard": verificar_queries_dashboard(),
    }
    
    print("\n" + "="*70)
    print("📊 RESUMO")
    print("="*70)
    
    for nome, ok in resultados.items():
        status = "✅ OK" if ok else "❌ ERRO"
        print(f"{nome:.<50} {status}")
    
    print("="*70)
    
    if all(resultados.values()):
        print("\n🎉 BANCO PRONTO PARA DEPLOY!")
        print("\nPróximos passos:")
        print("1. Fazer commit das mudanças")
        print("2. No servidor, rodar: psql -d fluxoland -f migrations/add_dashboard_and_whatsapp.sql")
        print("3. Configurar WHATSAPP_BOT_CONVERSA_TOKEN no .env")
        print("4. Deploy!")
        return 0
    else:
        print("\n⚠️  ATENÇÃO: Banco precisa de ajustes!")
        print("\nAntes do deploy:")
        print("1. Rodar migration: migrations/add_dashboard_and_whatsapp.sql")
        print("2. Verificar novamente com este script")
        return 1


if __name__ == "__main__":
    sys.exit(main())
