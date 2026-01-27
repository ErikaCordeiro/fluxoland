"""
Auto-migration: executa migrations pendentes automaticamente no startup
Útil para ambientes onde não há acesso SSH (Render free tier)
"""
from sqlalchemy import text, inspect
from database import engine, SessionLocal
import logging

logger = logging.getLogger(__name__)


def verificar_e_executar_migrations():
    """Verifica e executa migrations necessárias automaticamente"""
    try:
        db = SessionLocal()
        inspector = inspect(engine)
        
        # Verificar se coluna telefone existe em users
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'telefone' not in users_columns:
            logger.info("🔧 Executando migration: adicionando coluna users.telefone")
            db.execute(text("ALTER TABLE users ADD COLUMN telefone VARCHAR(20)"))
            db.commit()
            logger.info("✅ Coluna users.telefone criada")
        
        # Verificar se tipo tiponotificacao existe
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'tiponotificacao'
            )
        """)).scalar()
        
        if not result:
            logger.info("🔧 Executando migration: criando enum tiponotificacao")
            db.execute(text("CREATE TYPE tiponotificacao AS ENUM ('simulacao', 'cotacao', 'envio')"))
            db.commit()
            logger.info("✅ Enum tiponotificacao criado")
        else:
            # Verificar se valor 'envio' existe no enum
            envio_exists = db.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_enum 
                    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tiponotificacao')
                    AND enumlabel = 'envio'
                )
            """)).scalar()
            
            if not envio_exists:
                logger.info("🔧 Executando migration: adicionando valor 'envio' ao enum tiponotificacao")
                db.execute(text("ALTER TYPE tiponotificacao ADD VALUE 'envio'"))
                db.commit()
                logger.info("✅ Valor 'envio' adicionado ao enum tiponotificacao")
        
        # Verificar se tabela contatos_notificacao existe
        if 'contatos_notificacao' not in inspector.get_table_names():
            logger.info("🔧 Executando migration: criando tabela contatos_notificacao")
            db.execute(text("""
                CREATE TABLE contatos_notificacao (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    telefone VARCHAR(20) NOT NULL,
                    tipo tiponotificacao NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.execute(text("CREATE INDEX idx_contatos_notificacao_tipo ON contatos_notificacao(tipo)"))
            db.execute(text("CREATE INDEX idx_contatos_notificacao_ativo ON contatos_notificacao(ativo)"))
            db.commit()
            logger.info("✅ Tabela contatos_notificacao criada")
        
        # Verificar se colunas responsavel_vendedor e responsavel_telefone existem em propostas
        propostas_columns = [col['name'] for col in inspector.get_columns('propostas')]
        
        if 'responsavel_vendedor' not in propostas_columns:
            logger.info("🔧 Executando migration: adicionando coluna propostas.responsavel_vendedor")
            db.execute(text("ALTER TABLE propostas ADD COLUMN responsavel_vendedor VARCHAR(200)"))
            db.commit()
            logger.info("✅ Coluna propostas.responsavel_vendedor criada")
        
        if 'responsavel_telefone' not in propostas_columns:
            logger.info("🔧 Executando migration: adicionando coluna propostas.responsavel_telefone")
            db.execute(text("ALTER TABLE propostas ADD COLUMN responsavel_telefone VARCHAR(20)"))
            db.commit()
            logger.info("✅ Coluna propostas.responsavel_telefone criada")
        
        db.close()
        logger.info("🎉 Migrations concluídas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar migrations: {e}")
        if db:
            db.rollback()
            db.close()
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    verificar_e_executar_migrations()
