"""
Pega uma amostra de itens já aprovados do banco.db e exporta em dois arquivos:

  forms_perguntas.txt -> texto pra colar no Google Forms (uma pergunta por
                          bloco, já com as 4 alternativas)
  gabarito.csv         -> item_id, nivel, alternativa_correta
                          (NÃO mostrar pros respondentes, é só pra eu
                          corrigir depois e calcular dificuldade/discriminação)

É o jeito que achei de fazer o segundo survey sem precisar montar
login/sessão por respondente no Streamlit: monta um Forms rápido com os
itens que já passaram na validação por regras, pra ver se eles são bons
pedagogicamente (fácil/difícil demais, discrimina quem sabe de quem não
sabe) — pergunta diferente de "a LLM alucinou?".

Uso:
    python exportar_para_forms.py --nivel N5 --quantidade 12
    python exportar_para_forms.py --nivel N5 --nivel N4 --quantidade 12   # mistura os dois
"""

import argparse
import csv
import random
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "banco.db"


def buscar_itens(niveis: list[str], quantidade: int) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in niveis)
    cur = conn.execute(
        f"SELECT * FROM itens WHERE nivel_jlpt IN ({placeholders}) ORDER BY RANDOM() LIMIT ?",
        (*niveis, quantidade),
    )
    itens = [dict(row) for row in cur.fetchall()]
    conn.close()
    return itens


def montar_pergunta_formatada(numero: int, item: dict) -> str:
    """formato pra colar manualmente no Forms: cria uma pergunta de múltipla
    escolha, cola texto_jp como enunciado, e as 4 alternativas como opções"""
    return (
        f"=== Pergunta {numero} (nível {item['nivel_jlpt']}, item #{item['id']}) ===\n"
        f"Contexto: {item['texto_pt']}\n"
        f"Complete:\n{item['texto_jp']}\n"
        f"Alternativas:\n"
        f"A) {item['alternativa_a']}\n"
        f"B) {item['alternativa_b']}\n"
        f"C) {item['alternativa_c']}\n"
        f"D) {item['alternativa_d']}\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nivel", action="append", required=True, help="pode repetir: --nivel N5 --nivel N4")
    ap.add_argument("--quantidade", type=int, default=12)
    ap.add_argument("--seed", type=int, default=None, help="fixa a aleatoriedade pra reproduzir a mesma seleção depois")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if not DB_PATH.exists():
        print(f"Não encontrei {DB_PATH}. Rode isso na pasta banco_de_questoes, "
              f"depois de já ter gerado itens com o gerador_banco.py.")
        return

    itens = buscar_itens(args.nivel, args.quantidade)
    if not itens:
        print(f"Nenhum item aprovado encontrado para os níveis {args.nivel}. "
              f"Gere mais itens primeiro com o gerador_banco.py.")
        return
    if len(itens) < args.quantidade:
        print(f"Aviso: só havia {len(itens)} itens aprovados disponíveis "
              f"(você pediu {args.quantidade}). Exportando os {len(itens)} que existem.")

    # a ordem embaralhada já vem do ORDER BY RANDOM() do SQL, só numero aqui
    perguntas_texto = []
    gabarito_linhas = []
    for i, item in enumerate(itens, start=1):
        perguntas_texto.append(montar_pergunta_formatada(i, item))
        gabarito_linhas.append({
            "numero_no_forms": i,
            "item_id": item["id"],
            "nivel": item["nivel_jlpt"],
            "alternativa_correta": item["alternativa_correta"],
        })

    saida_txt = Path(__file__).parent / "forms_perguntas.txt"
    saida_txt.write_text("\n".join(perguntas_texto), encoding="utf-8")

    saida_csv = Path(__file__).parent / "gabarito.csv"
    with open(saida_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["numero_no_forms", "item_id", "nivel", "alternativa_correta"])
        writer.writeheader()
        writer.writerows(gabarito_linhas)

    print(f"Exportado {len(itens)} itens.")
    print(f"  Perguntas (cole no Forms): {saida_txt}")
    print(f"  Gabarito (NÃO mostre aos respondentes): {saida_csv}")


if __name__ == "__main__":
    main()
