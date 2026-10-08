import spacy
import random

# Liga/desliga um modo de debug pra ver como o spaCy está analisando a frase
modo_debug = True

# Carrega o modelo de português (é o que permite identificar verbo, substantivo, etc.)
nlp = spacy.load("pt_core_news_sm")

# Lista de frases que vão virar questões
frases = [
    "Eu comi arroz ontem",
    "Eu bebi água ontem",
    "Eu comi carne ontem",
    "Eu comi peixe ontem"
]

# Dicionário simples: português -> kanji correspondente
dicionario = {
    "arroz": "米",
    "água": "水",
    "carne": "肉",
    "peixe": "魚"
}

# Base de apoio com:
# - significado do kanji
# - kanjis parecidos (usados como alternativas erradas)
kanji_info = {
    "米": {"significado": "arroz", "parecidos": ["木", "本", "来"]},
    "水": {"significado": "água", "parecidos": ["氷", "永", "泉"]},
    "肉": {"significado": "carne", "parecidos": ["内", "人", "入"]},
    "魚": {"significado": "peixe", "parecidos": ["鳥", "島", "馬"]},

    # Kanjis usados como distratores (precisam ter significado para o feedback)
    "木": {"significado": "árvore"},
    "本": {"significado": "livro"},
    "来": {"significado": "vir"},
    "氷": {"significado": "gelo"},
    "永": {"significado": "eterno"},
    "泉": {"significado": "fonte"},
    "内": {"significado": "dentro"},
    "人": {"significado": "pessoa"},
    "入": {"significado": "entrar"},
    "鳥": {"significado": "pássaro"},
    "島": {"significado": "ilha"},
    "馬": {"significado": "cavalo"},
}

# Variável pra controlar quantos acertos o usuário teve
pontuacao = 0

# Loop principal: percorre cada frase e transforma em uma questão
for i, frase_pt in enumerate(frases):

    print(f"\n--- Questão {i+1} ---")

    # spaCy analisa a frase (aqui acontece o PLN)
    doc = nlp(frase_pt)

    # Se o debug estiver ligado, mostra como a frase foi interpretada
    if modo_debug:
        print("\nAnálise da frase:")
        for token in doc:
            print(f"{token.text} → {token.pos_} ({token.dep_})")

    # Aqui o sistema tenta descobrir qual palavra da frase virar exercício
    palavra_alvo = None

    for token in doc:
        # Regra simples: pegar substantivo que esteja no dicionário
        if token.pos_ == "NOUN" and token.text in dicionario:
            palavra_alvo = token.text

    # Se não encontrar nada válido, pula a questão
    if palavra_alvo is None:
        print("Erro ao gerar questão.")
        continue

    # Pega o kanji correto a partir da palavra encontrada
    kanji_correto = dicionario[palavra_alvo]

    # Busca os kanjis parecidos para usar como alternativas erradas
    parecidos = kanji_info[kanji_correto]["parecidos"]

    # Monta a lista de opções (1 correta + 3 erradas)
    opcoes = [kanji_correto] + parecidos

    # Embaralha as opções pra não ficar sempre na mesma posição
    random.shuffle(opcoes)

    # Frase base em japonês com lacuna (modelo fixo por enquanto)
    frase_jp = "昨日、___ を 食べました。"

    # Mostra a questão para o usuário
    print("\nFrase:")
    print(frase_pt)

    print("\nComplete:")
    print(frase_jp)

    print("\nOpções:")
    for j, opcao in enumerate(opcoes):
        print(f"{j+1}. {opcao}")

    # Recebe a resposta do usuário
    escolha = int(input("\nResposta: "))
    resposta = opcoes[escolha - 1]

    # Verifica se acertou ou errou
    if resposta == kanji_correto:
        print(" Correto!")
        pontuacao += 1
    else:
        print(" Errado!")

        # Feedback básico comparando o correto com o escolhido
        print(f"Correto: {kanji_correto} ({kanji_info[kanji_correto]['significado']})")
        print(f"Você marcou: {resposta} ({kanji_info[resposta]['significado']})")

        print("\nDica: observe as diferenças visuais entre os kanjis.")

# Mostra o resultado final depois de todas as questões
print("\n====================")
print(f"Pontuação final: {pontuacao}/4")