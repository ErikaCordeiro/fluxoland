import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import re
import unicodedata


class BlingParserService:
    """
    Lê e interpreta o HTML público do Bling (doc.view.php)
    Retorna dados estruturados para importação.
    NÃO grava nada no banco.
    """

    # ======================================================
    # ENTRYPOINT
    # ======================================================
    @staticmethod
    def parse_doc_view(link: str) -> dict:
        id_bling = BlingParserService._extrair_id_bling(link)

        response = requests.get(
            link,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (FluxoLand)"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        cliente = BlingParserService._extrair_cliente(soup)
        pedido = BlingParserService._extrair_dados_pedido(soup)
        itens = BlingParserService._extrair_itens(soup)

        return {
            "id_bling": id_bling,
            "cliente": cliente,
            "pedido": pedido,
            "itens": itens,
        }

    # ======================================================
    # ID BLING
    # ======================================================
    @staticmethod
    def _extrair_id_bling(link: str) -> str:
        parsed = urlparse(link)
        query = parse_qs(parsed.query)

        if "id" not in query or not query["id"]:
            raise ValueError("Link do Bling inválido (parâmetro id não encontrado)")

        return query["id"][0]

    # ======================================================
    # CLIENTE
    # ======================================================
    @staticmethod
    def _extrair_cliente(soup: BeautifulSoup) -> dict:
        texto = soup.get_text("\n", strip=True)

        # ESTRATÉGIA: Buscar seção "Para:" ou "Destinatário" (evitando "De:" / "Remetente" que é a AM Ferramentas)
        # Extrair bloco de texto após a palavra-chave e processar as linhas sequenciais
        
        nome = None
        documento = None
        endereco = None
        cidade = None
        
        # Procurar seção "Para:" ou similar (cliente/destinatário)
        m_para = re.search(r"(?:Para|Destinat[áa]rio)[:\s]*\n(?P<body>.{0,800})", texto, re.IGNORECASE | re.DOTALL)
        
        if m_para:
            body = m_para.group("body")
            lines = [l.strip() for l in body.splitlines() if l.strip()]
            
            # Primeira linha não vazia após "Para:" geralmente é o nome do cliente
            if lines:
                nome = lines[0]
                # Limpar possíveis labels residuais
                nome = re.sub(r"^(Para[:\s]*|Destinat[áa]rio[:\s]*)", "", nome, flags=re.IGNORECASE).strip()
            
            # Procurar CNPJ ou CPF nas linhas seguintes
            for i, ln in enumerate(lines):
                # Buscar CNPJ (formato brasileiro com pontos, barras e hífens)
                m_cnpj = re.search(r"(?:CNPJ|CPF)\s*[:]?\s*([0-9./-]{6,})", ln, re.IGNORECASE)
                if m_cnpj:
                    documento = m_cnpj.group(1).strip()
                    # Endereço geralmente vem logo após o CNPJ/CPF
                    if i + 1 < len(lines):
                        endereco = lines[i + 1]
                    # Cidade geralmente vem depois do endereço
                    if i + 2 < len(lines):
                        cidade = lines[i + 2]
                    break
        
        # Fallback: se não encontrou na seção "Para:", buscar em todo o texto
        if not nome:
            for chave in ("Para:", "Destinatário:", "Cliente:"):
                nome = BlingParserService._buscar_valor(texto, chave, default=None)
                if nome:
                    break
        
        if not documento:
            # Buscar CNPJ/CPF, mas EVITAR o da AM Ferramentas (23.224.473/0001-78)
            all_docs = re.findall(r"(?:CNPJ|CPF)\s*[:]?\s*([0-9./-]{6,})", texto, re.IGNORECASE)
            for doc in all_docs:
                # Pular se for o CNPJ da AM Ferramentas
                if "23.224.473/0001-78" not in doc and "23224473000178" not in doc.replace(".", "").replace("/", "").replace("-", ""):
                    documento = doc.strip()
                    break

        
        # Buscar telefone e email (geralmente aparecem após os dados do cliente)
        telefone = BlingParserService._buscar_valor(texto, "Fone:", "Telefone:", "Contato:", default=None)
        email = BlingParserService._buscar_email(texto)
        
        # Validação final: se ainda não encontrou nome, usar fallback
        if not nome or len(nome.strip()) < 2:
            nome = "Cliente Bling"

        return {
            "nome": nome,
            "documento": documento,
            "endereco": endereco,
            "cidade": cidade,
            "telefone": telefone,
            "email": email,
        }
        

    # ======================================================
    # DADOS DO PEDIDO
    # ======================================================
    @staticmethod
    def _extrair_dados_pedido(soup: BeautifulSoup) -> dict:
        texto = soup.get_text("\n", strip=True)

        # Extrai vendedor de forma mais robusta
        vendedor = None
        # Tenta buscar diretamente
        vendedor = BlingParserService._buscar_valor(texto, "Vendedor:", "Vendedor ", default=None)
        # Se não encontrou, tenta buscar na linha seguinte
        if not vendedor or len(vendedor.strip()) < 2:
            vendedor = BlingParserService._buscar_linha_apos(texto, "Vendedor", 0)
            if vendedor:
                # Remove a palavra "Vendedor:" se vier junto e prefixos como "(a):"
                vendedor = vendedor.replace("Vendedor:", "").replace("Vendedor", "").strip()
                # Remove prefixos do tipo "(a): NOME" -> "NOME"
                if vendedor.startswith("(a):") or vendedor.startswith("(a):"):
                    vendedor = vendedor.split(":", 1)[-1].strip()

        # Extrai valores da tabela de totais
        # A tabela tem 8 colunas na ordem:
        # Nº itens | Soma Qtdes | Total outros | Desconto total itens | Total itens | Desconto | Frete | Total proposta
        valores_totais = BlingParserService._extrair_valores_tabela_totais(texto)
        
        return {
            "numero": BlingParserService._buscar_valor(texto, "Proposta Nº", default=None),
            "data": BlingParserService._buscar_data(texto),
            "vendedor": vendedor if vendedor and len(vendedor.strip()) > 1 else None,
            "valor_produtos": valores_totais.get("total_itens"),
            "desconto": valores_totais.get("desconto"),
            "valor_frete": valores_totais.get("frete"),
            "valor_total": valores_totais.get("total_proposta"),
        }
    
    @staticmethod
    def _extrair_valores_tabela_totais(texto: str) -> dict:
        """
        Extrai os valores da tabela de totais do Bling.
        A tabela aparece após os cabeçalhos e tem 8 valores em sequência.
        """
        try:
            # Procura pela sequência de cabeçalhos da tabela de totais
            if "Total da proposta" not in texto:
                return {}
            
            # Divide o texto em linhas
            linhas = texto.split("\n")
            
            # Encontra a linha do cabeçalho "Total da proposta"
            idx_total_proposta = None
            for i, linha in enumerate(linhas):
                if "Total da proposta" in linha:
                    idx_total_proposta = i
                    break
            
            if idx_total_proposta is None:
                return {}
            
            # Os valores vêm nas próximas linhas após o cabeçalho
            # Coleta as próximas linhas que contenham números
            valores = []
            for i in range(idx_total_proposta + 1, min(idx_total_proposta + 15, len(linhas))):
                linha = linhas[i].strip()
                # Verifica se é uma linha com valor numérico
                if linha and any(c.isdigit() for c in linha):
                    try:
                        valor = float(
                            linha.replace("R$", "")
                            .replace(".", "")
                            .replace(",", ".")
                            .strip()
                        )
                        valores.append(valor)
                        if len(valores) >= 8:  # Já temos os 8 valores
                            break
                    except:
                        continue
            
            # Se conseguiu extrair pelo menos 8 valores, mapeia para os campos
            if len(valores) >= 8:
                return {
                    "num_itens": valores[0],
                    "soma_qtdes": valores[1],
                    "total_outros": valores[2],
                    "desconto_total_itens": valores[3],
                    "total_itens": valores[4],
                    "desconto": valores[5],
                    "frete": valores[6],
                    "total_proposta": valores[7],
                }
            
            return {}
        except Exception:
            return {}

    # ======================================================
    # ITENS / PRODUTOS
    # ======================================================
    @staticmethod
    def _extrair_itens(soup: BeautifulSoup) -> list[dict]:
        itens = []

        tabelas = soup.find_all("table")
        tabela_itens = None

        # procura tabela de itens por heurística de cabeçalhos
        for tabela in tabelas:
            ths = tabela.find_all("th")
            if not ths:
                continue
            headers = [th.get_text(strip=True) for th in ths]
            # normalize headers (remove accents, punctuation and lower)
            def _norm_head(h: str) -> str:
                tmp = unicodedata.normalize("NFKD", h)
                tmp = tmp.encode("ascii", "ignore").decode("ascii")
                return re.sub(r"[^0-9a-zA-Z]", "", tmp.lower())

            norm = [_norm_head(h) for h in headers]

            # procura por palavras-chave mínimas
            has_descr = any("descr" in h for h in norm)
            has_qtd = any(h.find("qtd") != -1 or h.find("qtde") != -1 or h.find("quant") != -1 for h in norm)
            if has_descr and has_qtd:
                tabela_itens = tabela
                header_norm = norm
                break

        if not tabela_itens:
            return itens

        # mapear índices de colunas por palavras-chave
        index_map = {}
        for i, h in enumerate(header_norm):
            if "descr" in h:
                index_map["nome"] = i
            if "ncm" in h:
                index_map["ncm"] = i
            if "cod" in h:
                index_map["codigo"] = i
            if "qtd" in h or "qtde" in h or "quant" in h:
                index_map["quantidade"] = i
            if "preco" in h and ("lista" in headers[i].lower() or "lista" in h):
                index_map["preco_lista"] = i
            if "preco" in h and ("un" in headers[i].lower() or "un." in headers[i].lower() or "un" in h):
                index_map["preco_unitario"] = i
            if "total" in h or "precototal" in h:
                index_map["preco_total"] = i

        linhas = tabela_itens.find_all("tr")[1:]
        for linha in linhas:
            colunas = linha.find_all("td")
            if not colunas:
                continue

            def get_col(key, default=None):
                idx = index_map.get(key)
                if idx is None or idx >= len(colunas):
                    return default
                return colunas[idx].get_text(strip=True)

            nome = get_col("nome", "").strip()
            codigo = get_col("codigo", "").strip()
            ncm = get_col("ncm", None)
            quantidade = BlingParserService._parse_int(get_col("quantidade", "1"))

            preco_unitario = None
            if index_map.get("preco_unitario") is not None:
                preco_unitario = BlingParserService._parse_float(get_col("preco_unitario", "0"))
            elif index_map.get("preco_lista") is not None:
                preco_unitario = BlingParserService._parse_float(get_col("preco_lista", "0"))

            preco_total = None
            if index_map.get("preco_total") is not None:
                preco_total = BlingParserService._parse_float(get_col("preco_total", "0"))
            else:
                preco_total = (preco_unitario or 0) * (quantidade or 1)

            itens.append({
                "codigo": codigo,
                "sku": codigo or None,
                "nome": nome,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "preco_total": preco_total,
                "ncm": ncm,
                "imagem_url": BlingParserService._extrair_imagem(linha),
            })

        return itens

    # ======================================================
    # HELPERS
    # ======================================================
    @staticmethod
    def _buscar_valor(texto: str, *chaves, default=None):
        for chave in chaves:
            if chave in texto:
                trecho = texto.split(chave, 1)[1]
                return trecho.split("\n")[0].strip()
        return default

    @staticmethod
    def _buscar_linha_apos(texto: str, chave: str, offset: int) -> str | None:
        linhas = texto.split("\n")
        for i, linha in enumerate(linhas):
            if chave in linha:
                try:
                    return linhas[i + offset].strip()
                except Exception:
                    return None
        return None

    @staticmethod
    def _buscar_email(texto: str) -> str | None:
        for parte in texto.split():
            if "@" in parte and "." in parte:
                return parte.strip()
        return None

    @staticmethod
    def _buscar_data(texto: str) -> datetime | None:
        for linha in texto.split("\n"):
            if "Data" in linha:
                try:
                    data_str = linha.split()[-1]
                    return datetime.strptime(data_str, "%d/%m/%Y")
                except Exception:
                    return None
        return None

    @staticmethod
    def _buscar_float(texto: str, chave: str) -> float | None:
        if chave not in texto:
            return None
        try:
            trecho = texto.split(chave, 1)[1]
            # Tenta pegar valor na mesma linha
            valor = trecho.split("\n")[0]
            
            # Se não tiver valor na mesma linha, tenta nas próximas 3 linhas
            if not any(c.isdigit() for c in valor):
                linhas = trecho.split("\n")
                for i in range(1, min(4, len(linhas))):
                    if any(c.isdigit() for c in linhas[i]):
                        valor = linhas[i]
                        break
            
            return float(
                valor.replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
        except Exception:
            return None

    @staticmethod
    def _extrair_imagem(linha) -> str | None:
        img = linha.find("img")
        if img and img.get("src"):
            return img["src"]
        return None

    @staticmethod
    def _parse_int(valor: str) -> int:
        try:
            v = str(valor).strip()
            # remove thousand separators and unify decimal separator to dot
            v = v.replace(".", "")
            v = v.replace(",", ".")
            f = float(v)
            return int(f) if f.is_integer() else int(round(f))
        except Exception:
            return 1

    @staticmethod
    def _parse_float(valor: str) -> float:
        try:
            return float(
                valor.replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
        except Exception:
            return 0.0
