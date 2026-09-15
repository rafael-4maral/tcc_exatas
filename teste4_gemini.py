import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ==================================
# CONFIGURAÇÃO DA API
# ==================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configurando o modelo principal para responder estritamente em JSON
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config={"response_mime_type": "application/json"}
)

model_feedback = genai.GenerativeModel("gemini-2.5-flash")

# ==================================
# ESCOLHA DO NÍVEL
# ==================================
print("\nEscolha o nível JLPT:")
print("1 - N5")
print("2 - N4")
print("3 - N3")
print("4 - N2")
print("5 - N1")

nivel_escolhido = input("\nDigite o número: ")
niveis = {"1": "N5", "2": "N4", "3": "N3", "4": "N2", "5": "N1"}
nivel = niveis.get(nivel_escolhido, "N5")

# ==================================
# ESCOLHA DO CONTEXTO
# ==================================
print("\nEscolha o contexto:")
print("1 - Cotidiano")
print("2 - Restaurante")
print("3 - Viagem")
print("4 - Faculdade")
print("5 - Trabalho")
print("6 - Cultura japonesa")
print("7 - Livre")

contextos = {
    "1": "Cotidiano",
    "2": "Restaurante",
    "3": "Viagem",
    "4": "Faculdade",
    "5": "Trabalho",
    "6": "Cultura japonesa",
    "7": "Livre"
}
contexto_escolhido = input("\nDigite o número: ")
contexto = contextos.get(contexto_escolhido, "Livre")

# ==================================
# PROMPT DE GERAÇÃO OTIMIZADO E CURTO
# ==================================
prompt_geracao = f"""
Você é um professor de japonês especializado em alunos brasileiros.
Crie um exercício Cloze curto e perfeitamente adaptado para um estudante brasileiro.

Nível JLPT exigido: {nivel}
Contexto do texto: {contexto}

TAMANHO DO TEXTO:
- O texto em japonês deve ser um parágrafo bem curto, contendo no máximo entre 2 e 3 linhas textuais. Seja conciso.

DIRETRIZES RÍGIDAS DE NIVELAMENTO (JLPT):

N5 (Iniciante):
- O texto deve ser curtíssimo e escrito QUASE TODO em hiragana e katakana.
- Use apenas estruturas gramaticais básicas (desu, masu, partículas simples wa, ga, wo, ni, de).
- NÃO utilize nenhum outro kanji além dos dois que serão ocultados nas lacunas. O restante do texto deve ser puramente kana.

N4 (Básico):
- Use estruturas e gramáticas simples do nível N4 (como ~te imaru, ~tai desu, ~tara, etc.).
- Além dos dois kanjis ocultados, você pode usar apenas de 2 a 3 kanjis extremamente básicos e comuns do nível N5 (como 日, 本, 人, 山). O restante deve ser kana.

N3 (Intermediário):
- Use gramática e vocabulário intermediário compatíveis com o nível N3.
- Misture kanjis de nível básico (N5/N4) e médio (N3) de forma equilibrada e natural com o kana, sem sobrecarregar o texto.

N2 (Pós-Intermediário):
- Use construções gramaticais e estruturas idiomáticas formais/escritas típicas do nível N2.
- A escrita deve ser predominantemente em kanjis (N5 até N2), mantendo o padrão esperado de leitura fluida deste nível.

N1 (Avançado):
- Utilize gramática complexa e escrita natural/fluida de nível nativo (estilo literário ou jornalístico do nível N1).

REGRAS DO EXERCÍCIO:
1. O parágrafo deve ser ambientado em um cenário, rotina ou situação conectada à realidade de um brasileiro.
2. O texto deve conter exatamente DUAS lacunas distintas marcadas estritamente como _____ e _____. Cada uma ocultará um Kanji diferente do nível {nivel}.
3. Gere exatamente 4 alternativas (A, B, C, D). Cada alternativa deve ser o par de Kanjis das duas lacunas (formato do valor: "Kanji1 / Kanji2").
4. Apenas uma alternativa deve estar correta. As outras devem conter distrações plausíveis baseadas em erros de radical ou leitura parecida.

Retorne os dados estritamente no formato JSON estruturado abaixo:

{{
  "texto_pt": "Tradução exata do parágrafo em português aqui",
  "texto_jp": "Parágrafo curto em japonês contendo as marcações _____ e _____ aqui",
  "alternativas": {{
    "A": "Kanji1 / Kanji2",
    "B": "Kanji1 / Kanji2",
    "C": "Kanji1 / Kanji2",
    "D": "Kanji1 / Kanji2"
  }},
  "alternativa_correta": "Letra correspondente ao par correto (A, B, C ou D)"
}}
"""

print(f"\nGerando exercícios adaptados para o nível {nivel}. Por favor, aguarde...")
response_exercicio = model.generate_content(prompt_geracao)

try:
    dados_exercicio = json.loads(response_exercicio.text)
except Exception as e:
    print("\nErro ao processar o formato do exercício. Tente rodar o script novamente.")
    exit()

# ==================================
# APRESENTAÇÃO DO EXERCÍCIO
# ==================================
print("\n==============================")
print("EXERCÍCIO GERADO")
print("==============================\n")

print(f"CONTEXTO EM PORTUGUÊS:\n{dados_exercicio['texto_pt']}\n")
print(f"TEXTO EM JAPONÊS:\n{dados_exercicio['texto_jp']}\n")
print("ALTERNATIVAS (Lacuna 1 / Lacuna 2):")
for letra, texto_alt in dados_exercicio['alternativas'].items():
    print(f"{letra}) {texto_alt}")
    
resposta_aluno = input("\nDigite a alternativa escolhida (A, B, C ou D): ").strip().upper()

correta = dados_exercicio['alternativa_correta'].strip().upper()
status_resultado = "ACERTOU" if resposta_aluno == correta else "ERRADO"

# ==================================
# PROMPT DE FEEDBACK CUSTOMIZADO
# ==================================
prompt_feedback = f"""
Você é um professor de japonês especializado em alunos brasileiros.
O aluno acabou de responder um exercício de preenchimento de lacunas com dois Kanjis. Forneça o feedback pedagógico baseado nos dados abaixo.

Exercício original:
Contexto PT: {dados_exercicio['texto_pt']}
Texto JP: {dados_exercicio['texto_jp']}
Alternativas: A) {dados_exercicio['alternativas']['A']}, B) {dados_exercicio['alternativas']['B']}, C) {dados_exercicio['alternativas']['C']}, D) {dados_exercicio['alternativas']['D']}

Gabarito Real da Questão: {correta} (Kanjis: {dados_exercicio['alternativas'].get(correta)})
Resposta marcada pelo Aluno: {resposta_aluno} (Kanjis: {dados_exercicio['alternativas'].get(resposta_aluno, "Opção inválida")})
Status do Aluno: {status_resultado}

Sua tarefa de feedback:

Se o status for ACERTOU:
- Dê os parabéns de forma amigável.
- Explique diretamente o significado, uso e leitura dos dois Kanjis corretos dentro daquele parágrafo.
- Mostre um exemplo prático curto para cada um deles.

Se o status for ERRADO:
- Explique claramente por que a alternativa escolhida pelo aluno está incorreta no contexto daquelas frases (mostre onde ocorreu o erro, se foi na lacuna 1, na lacuna 2 ou em ambas).
- Explique minuciosamente o significado, o uso e as leituras adequadas dos dois Kanjis da alternativa correta ({correta}).
- Aponte os detalhes visuais ou semânticos que diferenciam os Kanjis que geraram a confusão.
- Use referências ou analogias próximas da realidade brasileira para facilitar a fixação.

Finalize obrigatoriamente com:
- Uma dica prática de memorização visual ou mnemônica voltada exclusivamente para os Kanjis corretos da questão.

REGRAS CRUCIAIS DE FORMATAÇÃO (LEIA COM ATENÇÃO):
- NÃO use NENHUMA formatação Markdown ou sintaxe especial no seu texto.
- É terminantemente PROIBIDO o uso de asteriscos (como ** ou *) para destacar palavras.
- NÃO utilize hashtags (#) para simular títulos ou divisões.
- Escreva um texto completamente limpo, puro e perfeitamente legível para terminais de texto tradicionais.
- Use quebras de linha duplas para separar os blocos de texto.
- Para sinalizar títulos de seções, use apenas LETRAS MAIÚSCULAS simples (exemplo: RESULTADO DA AVALIAÇÃO:, DICA DE MEMORIZAÇÃO:).
- NÃO inclua seções de dicas gerais de estudo e NÃO gaste linhas explicando o significado isolado dos Kanjis errados fora do escopo da justificativa do erro.
"""

print("\nAnalisando sua resposta. Por favor, aguarde o feedback...")
feedback = model_feedback.generate_content(prompt_feedback)

print("\n==============================")
print("FEEDBACK DO PROFESSOR")
print("==============================\n")
print(feedback.text)
print("\n==============================")