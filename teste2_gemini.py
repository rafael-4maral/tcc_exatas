import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

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

niveis = {
    "1": "N5",
    "2": "N4",
    "3": "N3",
    "4": "N2",
    "5": "N1"
}

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
# PROMPT DE GERAÇÃO
# ==================================

prompt = f"""
Você é um professor de japonês especializado em alunos brasileiros.

Crie um exercício Cloze para um estudante brasileiro.

Nível JLPT: {nivel}

Contexto: {contexto}

Regras:

- O exercício deve ser adequado ao nível escolhido.
- Mostre uma frase em português.
- Mostre uma frase em japonês.
- Substitua apenas UM kanji por ___.
- Gere exatamente 4 alternativas.
- Apenas uma deve estar correta.
- As alternativas erradas devem ser plausíveis.
- NÃO mostre a resposta correta.
- NÃO mostre o gabarito.
- NÃO explique a resposta ainda.

Regras adicionais por nível:

N5:
- A frase deve estar quase toda em hiragana.
- Não utilize outros kanjis além do que será ocultado.

N4:
- Utilize poucos kanjis básicos.
- O foco deve continuar sendo o kanji ocultado.

N3:
- Misture kanjis e kana normalmente.

N2:
- Utilize predominantemente kanjis.

N1:
- Utilize escrita japonesa natural e avançada.

O exercício deve avaliar apenas UM kanji.

Não utilize outros kanjis difíceis na frase.

O restante da frase deve ser facilmente compreensível para um estudante do nível informado.

Formato obrigatório:

FRASE EM PORTUGUÊS:
...

FRASE EM JAPONÊS:
...

ALTERNATIVAS:
A) ...
B) ...
C) ...
D) ...



"""

# ==================================
# GERAÇÃO DO EXERCÍCIO
# ==================================

response = model.generate_content(prompt)

# ==================================
# MOSTRAR EXERCÍCIO
# ==================================

print("\n==============================")
print("EXERCÍCIO GERADO")
print("==============================\n")

print(response.text)

# ==================================
# RESPOSTA DO ALUNO
# ==================================

resposta_aluno = input(
    "\nDigite a alternativa escolhida (A, B, C ou D): "
)

# ==================================
# PROMPT DE FEEDBACK
# ==================================

prompt_feedback = f"""
Você é um professor de japonês especializado em alunos brasileiros.

O aluno acabou de responder um exercício Cloze.

Exercício:

{response.text}

Resposta do aluno:
{resposta_aluno}

Sua tarefa:

1. Descubra qual era a alternativa correta.
2. Verifique se o aluno acertou ou errou.

Se acertou:
- dê os parabéns;
- explique o significado do kanji;
- mostre um exemplo simples.

Se errou:
- explique por que a alternativa está errada;
- explique o significado da alternativa correta;
- explique o significado da alternativa escolhida;
- destaque diferenças visuais entre os kanjis;
- utilize exemplos próximos da realidade brasileira.

Finalize com:
- uma dica de memorização;
- uma dica curta de estudo.

Responda de forma amigável e pedagógica.
"""

# ==================================
# GERAR FEEDBACK
# ==================================

feedback = model.generate_content(prompt_feedback)

# ==================================
# MOSTRAR FEEDBACK
# ==================================

print("\n==============================")
print("FEEDBACK DO PROFESSOR")
print("==============================\n")

print(feedback.text)