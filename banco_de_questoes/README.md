# Banco de questões + validação

Anotações rápidas de como essa parte funciona, pra eu não esquecer depois.

Ideia geral: toda vez que o Gemini gera um exercício, ele não vai direto pro
app. Primeiro passa pelo `validador.py`, e o resultado (aprovou ou não, e por
quê) fica salvo pra sempre no banco. O banco de questões (`itens`) é só o que
passou; o log de tudo que aconteceu (`geracoes`) é o que eu uso pra calcular a
taxa de violação que entra como resultado no TCC.

## Arquivos

- `schema.sql` - cria as tabelas `itens` (o banco em si) e `geracoes` (log de
  toda tentativa, aprovada ou não)
- `validador.py` - as 4 regras (duas lacunas, alternativa única, kana só em
  N5/N4, kanji restrito à lista do nível). Roda sozinho com `python
  validador.py`, não precisa da API pra isso
- `gerador_banco.py` - chama o Gemini em lote, valida, grava tudo. É o que eu
  rodo pra construir o banco (fora do Streamlit, é só linha de comando mesmo)
- `kanji_niveis/n5.json`, `n4.json` - listas de kanji por nível. Por enquanto
  é só amostra parcial pra testar o validador, preciso trocar pela lista
  oficial completa do JLPT antes de gerar o banco de verdade (tem lista boa
  no site da Tanos). N3/N2/N1 ainda nem existem, o validador simplesmente
  pula a regra de kanji-fora-da-lista quando o nível não tá cadastrado

## Como rodar

```bash
pip install google-generativeai python-dotenv
python gerador_banco.py --nivel N5 --quantidade 20
python gerador_banco.py --nivel N4 --quantidade 20
python gerador_banco.py --relatorio   # taxa de violação por nível/regra
```

Isso cria o `banco.db` na mesma pasta. Pra ver o que tem dentro:

```bash
sqlite3 banco.db "SELECT nivel_jlpt, texto_jp, alternativa_correta FROM itens LIMIT 5;"
```

## Como isso entra no app (`testeNovo.py`)

Hoje o app gera um item novo toda vez e não guarda nada, o que tá ok pra
protótipo mas não dá pra reaplicar o mesmo item pra respondentes diferentes
(precisa disso pra análise de dificuldade/discriminação). Quando o banco tiver
populado, a mudança é trocar o `model.generate_content(...)` por uma leitura
no SQLite:

```python
import sqlite3

def carregar_itens(nivel, contexto=None, limite=5):
    conn = sqlite3.connect("banco_de_questoes/banco.db")
    cur = conn.cursor()
    if contexto:
        cur.execute(
            "SELECT * FROM itens WHERE nivel_jlpt=? AND contexto=? ORDER BY RANDOM() LIMIT ?",
            (nivel, contexto, limite),
        )
    else:
        cur.execute(
            "SELECT * FROM itens WHERE nivel_jlpt=? ORDER BY RANDOM() LIMIT ?",
            (nivel, limite),
        )
    colunas = [d[0] for d in cur.description]
    itens = [dict(zip(colunas, linha)) for linha in cur.fetchall()]
    conn.close()
    return itens
```

Isso troca `st.session_state.dados_exercicio = json.loads(response.text)` por
`st.session_state.dados_exercicio = carregar_itens(nivel, contexto, limite=1)[0]`.
Os nomes dos campos (`texto_pt`, `texto_jp`, `alternativa_correta`...) são os
mesmos que o app já espera, só que `alternativa_a`..`alternativa_d` vêm em
colunas separadas em vez de um dict `alternativas` - é só remontar na hora de
exibir.

## Próximo passo

Rodar uma leva pequena primeiro (`--quantidade 10`) só pra ver se as listas
parciais de kanji e as regras tão pegando certo, antes de gastar cota da API
gerando o banco inteiro.
