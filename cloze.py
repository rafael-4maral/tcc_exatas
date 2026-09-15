import spacy

nlp = spacy.load("pt_core_news_sm")

frase_pt = "Eu comi sushi ontem"

doc = nlp(frase_pt)

# dicionário simples
dicionario = {
    "sushi": "寿司"
}

palavra_alvo = None

for token in doc:
    if token.pos_ == "NOUN":
        palavra_alvo = token.text

kanji = dicionario.get(palavra_alvo, "???")

frase_jp = "昨日、___ を 食べました。"

print("\nFrase em português:")
print(frase_pt)

print("\nComplete a frase:")
print(frase_jp)

opcoes = [kanji, "水", "車", "猫"]

for i, opcao in enumerate(opcoes):
    print(f"{i+1}. {opcao}")

escolha = int(input("\nEscolha: "))
resposta = opcoes[escolha - 1]

if resposta == kanji:
    print("\n Correto!")
else:
    print("\n Errado!")
    print(f"Resposta correta: {kanji}")