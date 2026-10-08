"""
Reaplica o validador atual em cima de tudo que já tá salvo na tabela
`geracoes`, sem gastar chamada nova de API.

Serve pra quando corrijo um bug no validador (tipo o das lacunas com espaço)
depois de já ter gerado itens: em vez de descartar e gerar de novo (gastando
cota), só rejulgo o que já existe com a regra corrigida.

O que faz:
  1. pega o resposta_bruta (JSON cru do Gemini) de cada linha de geracoes
  2. roda validar_item() de novo
  3. atualiza aprovado/regra_violada/detalhe_violacao em geracoes
  4. item que passou a ser aprovado e ainda não tava em `itens`, insere
  5. item que deixou de ser aprovado (raro), remove de `itens`

Uso:
    python revalidar.py            # revalida tudo
    python revalidar.py --nivel N5 # só um nível
"""

import argparse
import json
import sqlite3
from pathlib import Path

from validador import validar_item

DB_PATH = Path(__file__).parent / "banco.db"


def _extrair_kanjis_das_alternativas(item: dict) -> tuple[str, str]:
    correta = item["alternativa_correta"].strip().upper()
    valor = item["alternativas"][correta]
    partes = [p.strip() for p in valor.split("/")]
    if len(partes) != 2:
        return valor, ""
    return partes[0], partes[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nivel", default=None, help="revalida só este nível; se omitido, revalida todos")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.nivel:
        linhas = conn.execute(
            "SELECT * FROM geracoes WHERE nivel_jlpt = ?", (args.nivel,)
        ).fetchall()
    else:
        linhas = conn.execute("SELECT * FROM geracoes").fetchall()

    contagem = {"virou_aprovado": 0, "virou_reprovado": 0, "sem_mudanca": 0, "json_invalido": 0}

    for linha in linhas:
        try:
            item = json.loads(linha["resposta_bruta"])
        except json.JSONDecodeError:
            contagem["json_invalido"] += 1
            continue

        veredito = validar_item(item, linha["nivel_jlpt"])
        estava_aprovado = bool(linha["aprovado"])
        agora_aprovado = veredito["aprovado"]

        conn.execute(
            "UPDATE geracoes SET aprovado = ?, regra_violada = ?, detalhe_violacao = ? WHERE id = ?",
            (int(agora_aprovado), veredito["regra_violada"], veredito["detalhe"], linha["id"]),
        )

        if agora_aprovado and not estava_aprovado:
            contagem["virou_aprovado"] += 1
            ja_existe = conn.execute(
                "SELECT 1 FROM itens WHERE log_id = ?", (linha["id"],)
            ).fetchone()
            if not ja_existe:
                kanji1, kanji2 = _extrair_kanjis_das_alternativas(item)
                conn.execute(
                    """INSERT INTO itens (nivel_jlpt, contexto, texto_pt, texto_jp, kanji1, kanji2,
                                            alternativa_a, alternativa_b, alternativa_c, alternativa_d,
                                            alternativa_correta, feedback_acertou, feedback_errou,
                                            origem, log_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'llm', ?)""",
                    (linha["nivel_jlpt"], linha["contexto"], item["texto_pt"], item["texto_jp"],
                     kanji1, kanji2, item["alternativas"]["A"], item["alternativas"]["B"],
                     item["alternativas"]["C"], item["alternativas"]["D"],
                     item["alternativa_correta"], item.get("feedback_se_acertou"),
                     item.get("feedback_se_errou"), linha["id"]),
                )
        elif estava_aprovado and not agora_aprovado:
            contagem["virou_reprovado"] += 1
            conn.execute("DELETE FROM itens WHERE log_id = ?", (linha["id"],))
        else:
            contagem["sem_mudanca"] += 1

    conn.commit()
    conn.close()

    print(f"Revalidação concluída em {len(linhas)} registros:")
    print(f"  passaram a ser APROVADOS: {contagem['virou_aprovado']}")
    print(f"  passaram a ser REPROVADOS: {contagem['virou_reprovado']}")
    print(f"  sem mudança: {contagem['sem_mudanca']}")
    if contagem["json_invalido"]:
        print(f"  (ignorados por JSON inválido: {contagem['json_invalido']})")
    print("\nRode 'python gerador_banco.py --relatorio' pra ver os números atualizados.")


if __name__ == "__main__":
    main()
