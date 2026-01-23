"""Teste completo de exclusão de transportadora."""
from database import SessionLocal
from models import Transportadora, CotacaoFrete

db = SessionLocal()

print("=== Teste Completo: Exclusão de Transportadora ===\n")

# Cria uma transportadora de teste
teste = Transportadora(nome="TESTE_DELETE")
db.add(teste)
db.commit()
db.refresh(teste)
print(f"✓ Criada transportadora de teste: ID {teste.id} - {teste.nome}")

# Tenta deletar
print(f"\n--- Tentando deletar transportadora sem cotações ---")
t_id = teste.id
transportadora = db.get(Transportadora, t_id)

if transportadora:
    tem_cotacoes = db.query(CotacaoFrete).filter(CotacaoFrete.transportadora_id == t_id).count() > 0
    print(f"Tem cotações? {tem_cotacoes}")
    
    if not tem_cotacoes:
        print(f"Deletando transportadora ID {t_id}...")
        db.delete(transportadora)
        db.commit()
        print("✓ Deletada com sucesso!")
        
        # Verifica se realmente foi deletada
        verificacao = db.get(Transportadora, t_id)
        if verificacao is None:
            print("✓ Confirmado: transportadora não existe mais no banco")
        else:
            print("✗ ERRO: Transportadora ainda existe!")
    else:
        print("✗ Não pode deletar (tem cotações)")
else:
    print("✗ Transportadora não encontrada")

db.close()
print("\n✅ Teste concluído!")
