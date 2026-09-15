import streamlit as st
import google.generativeai as genai
import json

import os
from dotenv import load_dotenv

load_dotenv()

# ==================================
# CONFIGURAÇÃO DA API
# ==================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Modelo configurado para trazer o pacote completo estruturado em JSON
model = genai.GenerativeModel(
    "gemini-2.5-flash", 
    generation_config={"response_mime_type": "application/json"}
)

st.title("Tutor de Kanji com Inteligência Artificial")
st.subheader("Exercícios adaptados para estudantes brasileiros")

# ==================================
# SIDEBAR - CONFIGURAÇÕES
# ==================================
with st.sidebar:
    st.header("Configurações")
    nivel = st.selectbox("Escolha o nível JLPT:", ["N5", "N4", "N3", "N2", "N1"])
    contexto = st.selectbox("Escolha o contexto:", 
                            ["Cotidiano", "Restaurante", "Viagem", "Faculdade", "Trabalho", "Cultura japonesa", "Livre"])

# Inicializando os estados de memória do Streamlit
if "dados_exercicio" not in st.session_state:
    st.session_state.dados_exercicio = None
if "resposta_enviada" not in st.session_state:
    st.session_state.resposta_enviada = False

# Botão para Gerar o Exercício
if st.button("Gerar Novo Exercício"):
    st.session_state.resposta_enviada = False
    st.session_state.dados_exercicio = None
    
    prompt_geracao = f"""
    Você é um professor de japonês para brasileiros focado na preparação para o JLPT.
    Crie um exercício Cloze em JSON para o nível {nivel} no contexto {contexto}.

    REFERÊNCIAS DE EXERCÍCIOS REAIS DO EXAME (Siga rigorosamente este padrão de estrutura, escrita e naturalidade):
    1. "これは 一つ___(1)___ いくらですか。――― 三百円___(2)___です。" -> Kanjis ocultados: 一つ (ひとつ) / 三百円 (さんびゃくえん)
    2. "わたしの たんじょうびは 五月五日___(1)___です。こどもの 日___(2)___とおなじです。" -> Kanjis ocultados: 五月五日 (ごがついつか) / 日 (ひ)
    3. "バスツアーの お金___(1)___は こんしゅうの 土よう日___(2)___までに はらってください。" -> Kanjis ocultados: お金 (おかね) / 土曜日 (どようび)
    4. "川___(1)___のそばに おおきい さくらの 木___(2)___がありました。" -> Kanjis ocultados: 川 (かわ) / 木 (き)
    5. "ペットボトルの 水___(1)___を 半分___(2)___のみました。" -> Kanjis ocultados: 水 (みず) / 半分 (はんぶん)
    6. "ビルの 上___(1)___から きれいな 月___(2)___がみえました。" -> Kanjis ocultados: 上 (うえ) / 月 (つき)
    7. "山下___(1)___さんですね。どうぞ 中___(2)___へ。" -> Kanjis ocultados: 山下 (やました) / 中 (なか)
    8. "あの 木___(1)___の 下___(2)___で やすみましょう。" -> Kanjis ocultados: 木 (き) / 下 (した)
    9. "あの 女の子___(1)___は テニスが 上手___(2)___ですね。" -> Kanjis ocultados: 女の子 (おんなのこ) / 上手 (じょうず)
    10. "えきの 東口___(1)___で 先生___(2)___に あいました。" -> Kanjis ocultados: 東口 (ひがしぐch) / 先生 (せんせい)

    REGRAS DE ESCRITA POR NÍVEL (RIGOROSO):
    - N5: O texto deve estar TODO em hiragana/katakana. É proibido usar qualquer outro kanji além dos dois ocultados.
    - N4: Texto predominantemente em kana. Permita apenas kanjis extremamente básicos de N5 (como 日, 本, 人). Foco nos dois ocultados.
    - N3: Mistura equilibrada de kanjis de nível N5 a N3 com kana.
    - N2/N1: Texto fluido com uso predominante de kanjis adequados ao nível avançado.

    REGRAS DO EXERCÍCIO:
    1. Monte um texto de leitura curto (um parágrafo contextualizado na realidade do Brasil).
    2. O texto precisa ter exatamente duas lacunas marcadas como ___(1)___ e ___(2)___ para ocultar dois Kanjis do nível {nivel}.
    3. Crie 4 alternativas (A, B, C, D) no formato "Kanji1 / Kanji2". Apenas uma é a correta. Crie distratores inteligentes baseados em erros comuns de leitura ou em radicais de escrita visualmente parecidos (ex: 土 vs 士 ou 千 vs 干).
    4. Os feedbacks devem ser ULTRA-CURTOS e concisos (máximo de 3 frases), sem usar nenhum markdown ou asteriscos. Use LETRAS MAIÚSCULAS apenas para títulos de seção.

    Retorne estritamente neste formato JSON:
    {{
      "texto_pt": "Tradução do texto em português",
      "texto_jp": "Texto em japonês com as marcações ___(1)___ e ___(2)___",
      "alternativas": {{"A": "K1 / K2", "B": "K1 / K2", "C": "K1 / K2", "D": "K1 / K2"}},
      "alternativa_correta": "Letra correspondente",
      "feedback_se_acertou": "PARABÉNS! [Max 3 frases] Explique de forma super direta a leitura e significado dos dois kanjis corretos. Adicione uma dica mnemônica visual extremamente curta.",
      "feedback_se_errou": "EXPLICAÇÃO DO ERRO: [Max 3 frases] Explique de forma direta o motivo do erro (diferença sutil entre os kanjis das lacunas) e forneça a tradução/leitura correta com uma dica mnemônica ultra-rápida."
    }}
    """
    
    with st.spinner("Solicitando pacote pedagógico à IA..."):
        try:
            response = model.generate_content(prompt_geracao)
            st.session_state.dados_exercicio = json.loads(response.text)
        except Exception as e:
            st.error(f"A API está sem cotas disponíveis no momento. Mensagem original: {e}")

# ==================================
# INTERFACE DO EXERCÍCIO
# ==================================
if st.session_state.dados_exercicio:
    dados = st.session_state.dados_exercicio
    
    st.info(f"**CONTEXTO EM PORTUGUÊS:**\n\n{dados['texto_pt']}")
    st.markdown("### TEXTO EM JAPONÊS:")
    st.code(dados['texto_jp'], language="text")
    
    st.markdown("### SELECIONE A OPÇÃO CORRETA (Lacuna 1 / Lacuna 2):")
    opcoes = [f"{letra}) {alt}" for letra, alt in dados['alternativas'].items()]
    escolha = st.radio("Alternativas:", opcoes)
    
    if st.button("Enviar Resposta"):
        st.session_state.resposta_enviada = True
        
    if st.session_state.resposta_enviada:
        resposta_letra = escolha[0]
        correta = dados['alternativa_correta'].strip().upper()
        
        st.markdown("---")
        st.subheader("FEEDBACK DO PROFESSOR")
        
        if resposta_letra == correta:
            st.success(f"Resultado: Você escolheu a alternativa {resposta_letra} e ACERTOU!")
            st.text(dados['feedback_se_acertou'])
        else:
            st.error(f"Resultado: Você escolheu a alternativa {resposta_letra} e ERROU. A correta era a {correta}.")
            st.text(dados['feedback_se_errou'])