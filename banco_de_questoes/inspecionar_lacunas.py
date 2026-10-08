"""
Script de diagnóstico: mostra a resposta crua do Gemini dos itens reprovados
pela regra duas_lacunas, pra ver se é erro de verdade ou falso positivo do
validador (ex: Gemini usando parênteses de largura total do japonês tipo
（1）, que a regex não pega).

Uso:
    python inspecionar_lacunas.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "banco.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.execute(
    "SELECT id, resposta_bruta FROM geracoes "
    "WHERE aprovado = 0 AND regra_violada = 'duas_lacunas' "
    "ORDER BY id DESC LIMIT 10"
)
linhas = cur.fetchall()
conn.close()

if not linhas:
    print("Nenhum item reprovado por 'duas_lacunas' encontrado.")
else:
    for row in linhas:
        print("=" * 60)
        print(f"item id: {row['id']}")
        print(row["resposta_bruta"][:500])
    print("=" * 60)
    print(f"\nTotal mostrado: {len(linhas)}")
