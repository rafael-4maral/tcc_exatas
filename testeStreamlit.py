import streamlit as st
import google.generativeai as genai
import json

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    Você é um professor de japonês para brasileiros. Crie um exercício Cloze em JSON para o nível {nivel} no contexto {contexto}.

    REGRAS DE ESCRITA POR NÍVEL (RIGOROSO):
    - N5: O texto deve estar TODO em hiragana/katakana. É proibido usar qualquer outro kanji além dos dois ocultados.
    - N4: Texto predominantemente em kana. Permita apenas kanjis extremamente básicos de N5 (como 日, 本, 人). Foco nos dois ocultados.
    - N3: Mistura equilibrada de kanjis de nível N5 a N3 com kana.
    - N2/N1: Texto fluido com uso predominante de kanjis adequados ao nível avançado.

    REGRAS DO EXERCÍCIO:
    1. Monte um texto de leitura curto (um parágrafo contextualizado na realidade do Brasil).
    2. O texto precisa ter exatamente duas lacunas marcadas como ___(1)___ e ___(2)___ para ocultar dois Kanjis do nível {nivel}.
    3. Crie 4 alternativas (A, B, C, D) no formato "Kanji1 / Kanji2". Apenas uma é a correta.
    4. Crie antecipadamente os textos explicativos de feedback (sem usar NENHUM markdown ou asteriscos, use LETRAS MAIÚSCULAS para títulos) para caso o aluno acerte ou erre.

    Retorne estritamente neste formato JSON:
    {{
      "texto_pt": "Tradução do texto em português",
      "texto_jp": "Texto em japonês com as marcações ___(1)___ e ___(2)___",
      "alternativas": {{"A": "K1 / K2", "B": "K1 / K2", "C": "K1 / K2", "D": "K1 / K2"}},
      "alternativa_correta": "Letra correspondente",
      "feedback_se_acertou": "Parabéns! Explique aqui o significado, uso e leitura dos dois kanjis corretos com exemplos rápidos. Termine com uma DICA DE MEMORIZAÇÃO mnemônica visual para os dois.",
      "feedback_se_errou": "EXPLICAÇÃO DO ERRO: Explique objetivamente qual lacuna gerou o erro. Explique o significado e leitura corretos da alternativa certa apontando os detalhes visuais que causam confusão. Termine com uma DICA DE MEMORIZAÇÃO mnemônica visual para os dois kanjis corretos."
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