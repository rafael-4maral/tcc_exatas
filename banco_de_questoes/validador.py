"""
Validador por regras dos itens gerados pela LLM.

Cada regra devolve (ok: bool, detalhe: str). validar_item roda todas na
ordem e para na primeira que falhar. O resultado disso alimenta a tabela
`geracoes` e no fim é a taxa de violação por nível (resultado do TCC).

Import:
    from validador import validar_item, carregar_kanjis_do_nivel
"""

import json
import re
import unicodedata
from pathlib import Path

PASTA_NIVEIS = Path(__file__).parent / "kanji_niveis"

# o Gemini às vezes escreve "___(1)___" colado e às vezes "___ (1) ___" com
# espaço. os \s* toleram qualquer espaçamento, conta como a mesma marcação
PADRAO_LACUNA = r"___\s*\(\s*\d\s*\)\s*___"

# N4 acumula N5, N3 acumula N4+N5 etc (é assim que o JLPT funciona: quem
# tá em N3 já devia saber os kanjis de N5 e N4)
NIVEIS_ACUMULADOS = {
    "N5": ["n5"],
    "N4": ["n5", "n4"],
    "N3": ["n5", "n4", "n3"],
    "N2": ["n5", "n4", "n3", "n2"],
    "N1": ["n5", "n4", "n3", "n2", "n1"],
}


def nivel_totalmente_cadastrado(nivel: str) -> bool:
    """True só se todos os arquivos de kanji necessários pra esse nível (ele
    + os anteriores) já existem. Importa pq validar com uma lista parcial
    (ex: N2 só com n5+n4, sem n3/n2 ainda) reprovaria quase tudo — os kanjis
    de N2/N3 apareceriam como "fora da lista" só por a lista estar
    incompleta, não porque o item tá errado de verdade. Então a regra de
    kanji-fora-da-lista só roda quando o nível tá 100% cadastrado."""
    nivel = nivel.upper()
    if nivel not in NIVEIS_ACUMULADOS:
        raise ValueError(f"Nível desconhecido: {nivel}")
    return all((PASTA_NIVEIS / f"{arquivo}.json").exists() for arquivo in NIVEIS_ACUMULADOS[nivel])


def carregar_kanjis_do_nivel(nivel: str) -> set:
    """Carrega e acumula os kanjis permitidos até o nível dado. Se o arquivo
    de algum nível ainda não existir, ignora (assim dá pra ir completando
    aos poucos). Pra saber se a lista tá completa ou só parcial, usa
    nivel_totalmente_cadastrado."""
    nivel = nivel.upper()
    if nivel not in NIVEIS_ACUMULADOS:
        raise ValueError(f"Nível desconhecido: {nivel}")

    permitidos = set()
    for arquivo in NIVEIS_ACUMULADOS[nivel]:
        caminho = PASTA_NIVEIS / f"{arquivo}.json"
        if not caminho.exists():
            continue
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        permitidos.update(dados.get("kanjis", []))
    return permitidos


def _is_kanji(char: str) -> bool:
    # bloco unicode CJK
    return "一" <= char <= "鿿"


def _is_kana(char: str) -> bool:
    if "぀" <= char <= "ゟ":  # hiragana
        return True
    if "゠" <= char <= "ヿ":  # katakana
        return True
    return not _is_kanji(char)  # pontuação, número, romaji contam como "não-kanji"


def regra_kanji_fora_da_lista(item: dict, nivel: str) -> tuple[bool, str]:
    """Texto fora das lacunas não pode ter kanji fora da lista oficial
    acumulada até o nível. Só roda de fato quando o nível tá 100%
    cadastrado (ver nivel_totalmente_cadastrado) — com lista parcial
    reprovaria quase tudo errado."""
    if not nivel_totalmente_cadastrado(nivel):
        return True, f"lista de kanjis de {nivel} (ou de um nível anterior) ainda não cadastrada — regra pulada"

    permitidos = carregar_kanjis_do_nivel(nivel)
    texto = item["texto_jp"]
    texto_sem_lacunas = re.sub(PADRAO_LACUNA, "", texto)  # tira as marcações antes de checar

    fora_da_lista = sorted({c for c in texto_sem_lacunas if _is_kanji(c) and c not in permitidos})
    if fora_da_lista:
        return False, f"kanji(s) fora da lista de {nivel}: {', '.join(fora_da_lista)}"
    return True, ""


def regra_kana_only(item: dict, nivel: str) -> tuple[bool, str]:
    """N5: fora das lacunas tem que ser 100% kana, nenhum kanji solto
    tolerado. N4: pode kana livre + qualquer kanji já visto em N5 (puxa de
    kanji_niveis/n5.json, não é lista fixa). De N3 pra cima essa regra não
    se aplica mais (quem cuida é regra_kanji_fora_da_lista)."""
    nivel = nivel.upper()
    if nivel not in ("N5", "N4"):
        return True, "regra não se aplica a este nível"

    texto = item["texto_jp"]
    texto_sem_lacunas = re.sub(PADRAO_LACUNA, "", texto)
    kanjis_soltos = sorted({c for c in texto_sem_lacunas if _is_kanji(c)})

    if nivel == "N4":
        tolerados_n4 = carregar_kanjis_do_nivel("N5")
        kanjis_soltos = [k for k in kanjis_soltos if k not in tolerados_n4]

    if kanjis_soltos:
        return False, f"texto de {nivel} contém kanji fora das lacunas (deveria ser só kana ou kanji de nível anterior): {', '.join(kanjis_soltos)}"
    return True, ""


def regra_alternativa_unica(item: dict, nivel: str) -> tuple[bool, str]:
    """tem que ter exatamente uma alternativa correta e válida (A-D)"""
    letras_validas = {"A", "B", "C", "D"}
    correta = item.get("alternativa_correta", "").strip().upper()

    if correta not in letras_validas:
        return False, f"alternativa_correta='{correta}' não é uma letra válida (A-D)"

    alternativas = item.get("alternativas", {})
    if set(alternativas.keys()) != letras_validas:
        return False, f"esperava exatamente as chaves A,B,C,D em 'alternativas', recebeu {sorted(alternativas.keys())}"

    valores = list(alternativas.values())
    if len(set(valores)) != len(valores):
        return False, "duas ou mais alternativas têm o mesmo texto (empate na resposta)"

    return True, ""


def regra_duas_lacunas(item: dict, nivel: str) -> tuple[bool, str]:
    """texto precisa ter ___(1)___ e ___(2)___, uma vez cada (tolera espaço
    dentro da marcação, só o número importa)"""
    texto = item["texto_jp"]
    digitos = re.findall(r"___\s*\(\s*(\d)\s*\)\s*___", texto)
    if sorted(digitos) != ["1", "2"]:
        marcacoes = re.findall(PADRAO_LACUNA, texto)
        return False, f"esperava exatamente uma ocorrência de ___(1)___ e ___(2)___, encontrou: {marcacoes}"
    return True, ""


# ordem importa: regras estruturais/baratas primeiro, regras de conteúdo
# linguístico depois (assim erro de formatação não vira "alucinação de vocabulário")
REGRAS = [
    ("duas_lacunas", regra_duas_lacunas),
    ("alternativa_unica", regra_alternativa_unica),
    ("kana_only", regra_kana_only),
    ("kanji_fora_da_lista", regra_kanji_fora_da_lista),
]


def validar_item(item: dict, nivel: str) -> dict:
    """roda as regras em ordem, para na primeira que falhar.
    retorna {"aprovado": bool, "regra_violada": str|None, "detalhe": str}"""
    for nome_regra, funcao in REGRAS:
        ok, detalhe = funcao(item, nivel)
        if not ok:
            return {"aprovado": False, "regra_violada": nome_regra, "detalhe": detalhe}
    return {"aprovado": True, "regra_violada": None, "detalhe": ""}


def validar_item_completo(item: dict, nivel: str) -> dict:
    """mesma coisa mas roda TODAS as regras (não para na primeira), útil
    pra debugar manualmente. pra métrica do TCC usa validar_item mesmo"""
    violacoes = []
    for nome_regra, funcao in REGRAS:
        ok, detalhe = funcao(item, nivel)
        if not ok:
            violacoes.append({"regra": nome_regra, "detalhe": detalhe})
    return {"aprovado": len(violacoes) == 0, "violacoes": violacoes}


if __name__ == "__main__":
    # teste manual rápido, roda sem precisar da API
    item_bom_n5 = {
        "texto_jp": "きょう、___(1)___で ___(2)___を たべました。",
        "alternativas": {"A": "がっこう / さかな", "B": "X", "C": "Y", "D": "Z"},
        "alternativa_correta": "A",
    }
    item_ruim_n5 = {
        # tem 食 fora das lacunas, deveria ser só kana em N5
        "texto_jp": "きょう、___(1)___で 食べました___(2)___。",
        "alternativas": {"A": "がっこう / さかな", "B": "X", "C": "Y", "D": "Z"},
        "alternativa_correta": "A",
    }
    print("Item bom  :", validar_item(item_bom_n5, "N5"))
    print("Item ruim :", validar_item(item_ruim_n5, "N5"))
