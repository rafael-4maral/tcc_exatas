# Sistema Cloze simples para kanji

# frase original
frase_pt = "Eu comi sushi ontem"

# frase em japonês com lacuna
frase_jp = "昨日、___ を 食べました。"

# alternativas de kanji
opcoes = ["寿司", "水", "車", "猫"]

# resposta correta
resposta_correta = "寿司"

print("\nFrase em português:")
print(frase_pt)

print("\nComplete a frase em japonês:")
print(frase_jp)

print("\nOpções:")
for i, opcao in enumerate(opcoes):
    print(f"{i+1}. {opcao}")

# input do usuário
escolha = int(input("\nEscolha a opção correta: "))
resposta_usuario = opcoes[escolha - 1]

# verificação
if resposta_usuario == resposta_correta:
    print("\n Correto!")
else:
    print("\n Incorreto.")
    print(f"Resposta correta: {resposta_correta}")

import spacy

# carrega modelo de português
nlp = spacy.load("pt_core_news_sm")

# frase original
frase_pt = "Eu comi sushi ontem"

doc = nlp(frase_pt)



print("\nAnalisando frase:\n")

# detectar substantivos (possíveis palavras para kanji)
palavras_alvo = []

for token in doc:
    print(f"{token.text} → {token.pos_}")
    
    if token.pos_ == "NOUN":
        palavras_alvo.append(token.text)

print("\nPalavras candidatas para exercício:")
print(palavras_alvo)



# mapeamento simples (protótipo)
dicionario = {
    "sushi": "寿司"
}

palavra = palavras_alvo[0]

kanji = dicionario.get(palavra, "???")

frase_jp = f"昨日、___ を 食べました。"

print("\nComplete a frase:")
print(frase_jp)

opcoes = [kanji, "水", "車", "猫"]

for i, opcao in enumerate(opcoes):
    print(f"{i+1}. {opcao}")