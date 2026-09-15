import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# ESCOLHA DO NÍVEL

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


# ESCOLHA DO CONTEXTO

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
# PROMPT
# ==================================

prompt = f"""
Você é um professor de japonês especializado em alunos brasileiros.

Sua função é criar exercícios pedagógicos para estudantes brasileiros de japonês.

Nível do aluno: {nivel}

Contexto escolhido: {contexto}

Crie APENAS UM exercício do tipo Cloze.

Regras:

- O exercício deve estar adequado ao nível informado.
- Mostre primeiro a frase em português.
- Depois mostre a frase em japonês.
- Substitua apenas UM kanji por ___.
- Gere exatamente 4 alternativas.
- Apenas uma alternativa deve ser correta.
- As alternativas incorretas devem ser plausíveis.
- Não explique a resposta ainda.
- Não forneça feedback ainda.

Formato obrigatório:

FRASE EM PORTUGUÊS:
...

FRASE EM JAPONÊS:
...

ALTERNATIVAS:
A)
B)
C)
D)

Não mostre a resposta correta.
Não mostre o gabarito.

# CHAMADA AO GEMINI

response = model.generate_content(prompt)


# EXIBIÇÃO

print("\n==============================")
print("EXERCÍCIO GERADO")
print("==============================\n")
"""
print(response.text)