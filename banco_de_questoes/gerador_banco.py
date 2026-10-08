"""
Gera itens em lote com o Gemini, valida cada um (validador.py) e salva tudo
no SQLite: os aprovados vão pra tabela `itens` (banco de questões) e TODAS
as tentativas (aprovadas ou não) vão pra `geracoes`. É essa segunda tabela
que uso depois pra calcular a taxa de violação/alucinação no TCC.

Uso:
    python gerador_banco.py --nivel N5 --contexto Cotidiano --quantidade 10
    python gerador_banco.py --nivel N5 --quantidade 30            # sorteia o contexto
    python gerador_banco.py --relatorio                           # só imprime as taxas

Precisa do GEMINI_API_KEY no .env (mesmo esquema dos protótipos) e dos pacotes
google-generativeai e python-dotenv. Não precisa do Streamlit rodando pra isso.
"""

import argparse
import json
import os
import random
import sqlite3
import time
from pathlib import Path

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv

from validador import validar_item

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

DB_PATH = Path(__file__).parent / "banco.db"
MODELO_NOME = "gemini-2.5-flash"

# plano gratuito do Gemini só deixa 5 chamadas/min nesse modelo. 13s de
# intervalo dá uma folga em cima do limite teórico (60/5=12s)
PAUSA_ENTRE_CHAMADAS_SEGUNDOS = 13
MAX_TENTATIVAS_POR_ITEM = 3

CONTEXTOS_PADRAO = ["Cotidiano", "Restaurante", "Viagem", "Faculdade", "Trabalho", "Cultura japonesa"]

# prompt copiado do testeNovo.py pra manter o mesmo ajuste fino que já tinha
# lá. se mudar um, muda o outro tb (ou um dia junto os dois num só arquivo)
PROMPT_TEMPLATE = """
Você é um professor de japonês para brasileiros focado na preparação para o JLPT.
Crie um exercício Cloze em JSON para o nível {nivel} no contexto {contexto}.

REFERÊNCIAS DE EXERCÍCIOS REAIS DO EXAME (Siga rigorosamente este padrão de estrutura de escrita e simplicidade):
1. "これは 一つ___(1)___ いくらですか。――― 三百円___(2)___です。" -> Kanjis ocultados: 一つ (ひとつ) / 三百円 (さんびゃくえん)
2. "わたしの たんじょうびは 五月五日___(1)___です。こどもの 日___(2)___とおなじです。" -> Kanjis ocultados: 五月五日 (ごがついつか) / 日 (ひ)
3. "バスツアーの お金___(1)___は こんしゅうの 土よう日___(2)___までに はらってください。" -> Kanjis ocultados: お金 (おかね) / 土曜日 (どようび)
4. "川___(1)___のそばに おおきい さくらの 木___(2)___がありました。" -> Kanjis ocultados: 川 (かわ) / 木 (き)
5. "ペットボトルの 水___(1)___を 半分___(2)___のみました。" -> Kanjis ocultados: 水 (みず) / 半分 (はんぶん)

REGRAS DE ESCRITA POR NÍVEL (RIGOROSO):
- N5: O texto deve estar TODO em hiragana/katakana. É proibido usar qualquer outro kanji além dos dois ocultados.
- N4: Texto predominantemente em kana. Permita apenas kanjis extremamente básicos de N5 (como 日, 本, 人). Foco nos dois ocultados.
- N3: Mistura equilibrada de kanjis de nível N5 a N3 com kana.
- N2/N1: Texto fluido com uso predominante de kanjis adequados ao nível avançado.

REGRAS DO EXERCÍCIO:
1. Monte um texto de leitura curto (um parágrafo contextualizado na realidade do Brasil).
2. O texto precisa ter exatamente duas lacunas marcadas como ___(1)___ e ___(2)___ para ocultar dois Kanjis do nível {nivel}.
3. Crie 4 alternativas (A, B, C, D) no formato "Kanji1 / Kanji2". Apenas uma é a correta. Crie distratores inteligentes baseados em erros comuns de leitura ou em radicais de escrita visualmente parecidos (ex: 土 vs 士 ou 千 vs 干).

REGRAS DE FEEDBACK VOLTADAS PARA BRASILEIROS (MUITO IMPORTANTE):
O feedback pós-resposta deve ser equilibrado (entre 3 e 4 frases completas) e sem usar NENHUM markdown ou asterisco.
Você deve obrigatoriamente:
- Apontar de forma super direta onde o estudante brasileiro costuma errar ou se confundir visualmente.
- Fornecer uma dica de memorização mnemônica prática adaptada para a realidade cultural ou linguística do Brasil.
- Use LETRAS MAIÚSCULAS apenas para destacar títulos de seção.

Retorne estritamente neste formato JSON:
{{
  "texto_pt": "Tradução do texto em português",
  "texto_jp": "Texto em japonês com as marcações ___(1)___ e ___(2)___",
  "alternativas": {{"A": "K1 / K2", "B": "K1 / K2", "C": "K1 / K2", "D": "K1 / K2"}},
  "alternativa_correta": "Letra correspondente",
  "feedback_se_acertou": "...",
  "feedback_se_errou": "..."
}}
"""


def conectar_db():
    primeira_vez = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    if primeira_vez:
        schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
        conn.executescript(schema)
    return conn


def gerar_um_item(nivel: str, contexto: str) -> tuple[str, str]:
    """Chama o Gemini uma vez. Se bater o limite de cota (429), espera e
    tenta de novo. Retorna (prompt, resposta_crua) sem fazer parse do JSON
    ainda, pq quero guardar a resposta exatamente como veio, mesmo que não
    seja um JSON válido — também conta como violação."""
    model = genai.GenerativeModel(
        MODELO_NOME, generation_config={"response_mime_type": "application/json"}
    )
    prompt = PROMPT_TEMPLATE.format(nivel=nivel, contexto=contexto)

    for tentativa in range(1, MAX_TENTATIVAS_POR_ITEM + 1):
        try:
            response = model.generate_content(prompt)
            return prompt, response.text
        except ResourceExhausted as e:
            # a API costuma dizer quanto tempo esperar (retry_delay); uso
            # isso com 2s de folga em vez de um valor fixo chutado
            espera = getattr(getattr(e, "retry_delay", None), "seconds", None) or 20
            espera += 2
            print(f"    cota excedida (tentativa {tentativa}/{MAX_TENTATIVAS_POR_ITEM}), "
                  f"aguardando {espera}s antes de tentar de novo...")
            time.sleep(espera)

    # estourou as tentativas, deixa quebrar mesmo (melhor que fingir que gerou)
    response = model.generate_content(prompt)
    return prompt, response.text


def processar_item(conn, nivel: str, contexto: str):
    prompt, resposta_bruta = gerar_um_item(nivel, contexto)

    try:
        item = json.loads(resposta_bruta)
        item_valido_json = True
    except json.JSONDecodeError:
        item_valido_json = False
        item = None

    if item_valido_json:
        veredito = validar_item(item, nivel)
    else:
        veredito = {"aprovado": False, "regra_violada": "json_invalido", "detalhe": "resposta não é um JSON válido"}

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO geracoes (nivel_jlpt, contexto, prompt_enviado, resposta_bruta,
                                   aprovado, regra_violada, detalhe_violacao, modelo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (nivel, contexto, prompt, resposta_bruta, int(veredito["aprovado"]),
         veredito["regra_violada"], veredito["detalhe"], MODELO_NOME),
    )
    log_id = cur.lastrowid

    if veredito["aprovado"]:
        kanji1, kanji2 = _extrair_kanjis_das_alternativas(item)
        cur.execute(
            """INSERT INTO itens (nivel_jlpt, contexto, texto_pt, texto_jp, kanji1, kanji2,
                                    alternativa_a, alternativa_b, alternativa_c, alternativa_d,
                                    alternativa_correta, feedback_acertou, feedback_errou,
                                    origem, log_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'llm', ?)""",
            (nivel, contexto, item["texto_pt"], item["texto_jp"], kanji1, kanji2,
             item["alternativas"]["A"], item["alternativas"]["B"],
             item["alternativas"]["C"], item["alternativas"]["D"],
             item["alternativa_correta"], item.get("feedback_se_acertou"),
             item.get("feedback_se_errou"), log_id),
        )

    conn.commit()
    return veredito


def _extrair_kanjis_das_alternativas(item: dict) -> tuple[str, str]:
    """alternativa certa vem tipo 'K1 / K2', separa os dois pra gravar em
    colunas próprias (dá pra consultar tipo "quantos itens usam o kanji 水")"""
    correta = item["alternativa_correta"].strip().upper()
    valor = item["alternativas"][correta]
    partes = [p.strip() for p in valor.split("/")]
    if len(partes) != 2:
        return valor, ""
    return partes[0], partes[1]


def imprimir_relatorio(conn):
    """taxa de violação por nível, é esse número que vira resultado no TCC"""
    cur = conn.cursor()
    cur.execute(
        """SELECT nivel_jlpt,
                  COUNT(*) AS total,
                  SUM(aprovado) AS aprovados,
                  ROUND(100.0 * (COUNT(*) - SUM(aprovado)) / COUNT(*), 1) AS taxa_violacao_pct
           FROM geracoes
           GROUP BY nivel_jlpt
           ORDER BY nivel_jlpt"""
    )
    linhas = cur.fetchall()
    print(f"{'Nível':6} {'Total':>6} {'Aprovados':>10} {'Taxa de violação':>18}")
    for nivel, total, aprovados, taxa in linhas:
        print(f"{nivel:6} {total:>6} {aprovados:>10} {taxa:>17}%")

    print("\nViolações por regra:")
    cur.execute(
        """SELECT nivel_jlpt, regra_violada, COUNT(*)
           FROM geracoes WHERE aprovado = 0
           GROUP BY nivel_jlpt, regra_violada
           ORDER BY nivel_jlpt, COUNT(*) DESC"""
    )
    for nivel, regra, qtd in cur.fetchall():
        print(f"  {nivel:4} {regra:22} {qtd}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nivel", default="N5")
    ap.add_argument("--contexto", default=None, help="se não passar, sorteia um contexto a cada item")
    ap.add_argument("--quantidade", type=int, default=10)
    ap.add_argument("--relatorio", action="store_true")
    args = ap.parse_args()

    conn = conectar_db()

    if args.relatorio:
        imprimir_relatorio(conn)
        return

    for i in range(args.quantidade):
        contexto = args.contexto or random.choice(CONTEXTOS_PADRAO)
        veredito = processar_item(conn, args.nivel, contexto)
        status = "APROVADO" if veredito["aprovado"] else f"REPROVADO ({veredito['regra_violada']}: {veredito['detalhe']})"
        print(f"[{i+1}/{args.quantidade}] {args.nivel}/{contexto} -> {status}")

        # respeita o limite de 5 chamadas/min do plano gratuito (não espera no último item)
        if i < args.quantidade - 1:
            time.sleep(PAUSA_ENTRE_CHAMADAS_SEGUNDOS)

    print()
    imprimir_relatorio(conn)


if __name__ == "__main__":
    main()
