from models import PropostaHistorico

def registrar_historico(db, proposta, acao, descricao, usuario):
    evento = PropostaHistorico(
        proposta_id=proposta.id,
        acao=acao,
        descricao=descricao,
        usuario_nome=usuario.nome
    )
    db.add(evento)
