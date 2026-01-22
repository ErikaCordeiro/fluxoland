"""
Script para executar todas as migrações pendentes em produção.
Execute este script no terminal do Render ou localmente apontando para o banco de produção.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from database import DATABASE_URL

def run_migration(engine, migration_file, description):
    """Executa uma migração específica"""
    print(f"\n{'='*60}")
    print(f"Executando: {description}")
    print('='*60)
    
    try:
        # Lê o conteúdo do arquivo de migração
        migration_path = Path(__file__).parent / "migrations" / migration_file
        
        if not migration_path.exists():
            print(f"❌ Arquivo não encontrado: {migration_file}")
            return False
            
        # Extrai o SQL do arquivo
        with open(migration_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Procura pelo SQL no arquivo
        if 'ALTER TABLE' in content or 'UPDATE' in content:
            # Extrai as linhas de SQL
            lines = content.split('\n')
            sql_commands = []
            for line in lines:
                if 'db.execute(text(' in line or "db.execute(text('" in line:
                    # Extrai o SQL entre aspas
                    start = line.find('"""') if '"""' in line else line.find('"')
                    if start != -1:
                        sql_start = start + 3 if '"""' in line else start + 1
                        sql_end = line.find('"""', sql_start) if '"""' in line else line.find('"', sql_start)
                        if sql_end != -1:
                            sql = line[sql_start:sql_end].strip()
                            if sql:
                                sql_commands.append(sql)
            
            # Executa cada comando SQL
            with engine.connect() as conn:
                for sql in sql_commands:
                    print(f"\nExecutando SQL: {sql[:100]}...")
                    conn.execute(text(sql))
                    conn.commit()
                    
            print(f"✅ {description} executada com sucesso!")
            return True
        else:
            print(f"⚠️  Nenhum SQL encontrado em {migration_file}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar migração: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("EXECUTANDO MIGRAÇÕES EM PRODUÇÃO")
    print("="*60)
    print(f"Database: {DATABASE_URL.split('@')[-1]}")  # Mostra apenas o host
    
    # Cria engine
    engine = create_engine(DATABASE_URL)
    
    # Lista de migrações para executar
    migrations = [
        ("add_desconto_propostas.py", "Adicionar coluna 'desconto' na tabela propostas"),
        ("add_atualizado_em.py", "Adicionar coluna 'atualizado_em' na tabela propostas"),
    ]
    
    # Executa cada migração
    success_count = 0
    for migration_file, description in migrations:
        if run_migration(engine, migration_file, description):
            success_count += 1
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print(f"✅ Migrações executadas: {success_count}/{len(migrations)}")
    
    if success_count == len(migrations):
        print("\n🎉 Todas as migrações foram executadas com sucesso!")
        print("O sistema já pode ser acessado normalmente.")
    else:
        print("\n⚠️  Algumas migrações falharam. Verifique os erros acima.")
    
    engine.dispose()


if __name__ == "__main__":
    main()
