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

# ==================================
# INICIALIZAÇÃO DOS ESTADOS DE MEMÓRIA (STREAMLIT SESSION STATE)
# ==================================
if "num_exercicio" not in st.session_state:
    st.session_state.num_exercicio = 1
if "acertos" not in st.session_state:
    st.session_state.acertos = 0
if "historico" not in st.session_state:
    st.session_state.historico = []
if "dados_exercicio" not in st.session_state:
    st.session_state.dados_exercicio = None
if "resposta_enviada" not in st.session_state:
    st.session_state.resposta_enviada = False
if "fim_ciclo" not in st.session_state:
    st.session_state.fim_ciclo = False

# ==================================
# INTERFACE PRINCIPAL
# ==================================
st.title("Tutor de Kanji com Inteligência Artificial")
st.subheader("Exercícios adaptados para estudantes brasileiros")

# SIDEBAR - CONFIGURAÇÕES
with st.sidebar:
    st.header("Configurações")
    nivel = st.selectbox("Escolha o nível JLPT:", ["N5", "N4", "N3", "N2", "N1"])
    contexto = st.selectbox("Escolha o contexto:", 
                            ["Cotidiano", "Restaurante", "Viagem", "Faculdade", "Trabalho", "Cultura japonesa", "Livre"])
    
    st.markdown("---")
    st.info("💡 **Sobre o treino:** Cada sessão de estudos contém exatamente **5 exercícios** adaptados ao nível e contexto selecionados.")

# ==================================
# FLUXO DE EXIBIÇÃO: DASHBOARD FINAL OU EXERCÍCIO ATIVO
# ==================================

# ESTADO 1: FIM DO CICLO (MOSTRAR RESULTADOS)
if st.session_state.fim_ciclo:
    st.balloons()
    st.success("### 🎉 Treino Concluído com Sucesso!")
    
    # Dashboard de Performance
    taxa_acerto = (st.session_state.acertos / 5) * 100
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Sua Pontuação", value=f"{st.session_state.acertos} / 5", delta="Exercícios")
    with col2:
        st.metric(label="Taxa de Acertos", value=f"{taxa_acerto:.0f}%")
        
    # Mensagem motivacional baseada no desempenho
    if st.session_state.acertos == 5:
        st.markdown("**Perfeito! Aproveitamento de 100%! Você está dominando os kanjis desse nível!** 🏆")
    elif st.session_state.acertos >= 3:
        st.markdown("**Muito bom! Ótimo desempenho. Continue revisando os mnemônicos para gabaritar na próxima!** 🚀")
    else:
        st.markdown("**Não desanime! O aprendizado de Kanji é feito de repetição. Vamos tentar mais uma vez para fixar os conceitos!** 📚")
        
    # Histórico detalhado para revisão pedagógica
    st.markdown("### 📝 Histórico de Revisão:")
    for item in st.session_state.historico:
        icone = "✅" if item["resultado"] else "❌"
        with st.expander(f"Exercício {item['num']}: {icone} {item['texto_pt'][:40]}..."):
            st.markdown(f"**Frase em Japonês:** `{item['texto_jp']}`")
            st.markdown(f"**Tradução:** {item['texto_pt']}")
            st.markdown(f"**Sua Resposta:** {item['escolha']}")
            st.markdown(f"**Gabarito Correto:** Alternativa {item['correta']}")
            
    # Botão para reiniciar um novo ciclo
    if st.button("Iniciar Novo Ciclo (5 Exercícios)", type="primary"):
        st.session_state.num_exercicio = 1
        st.session_state.acertos = 0
        st.session_state.historico = []
        st.session_state.dados_exercicio = None
        st.session_state.resposta_enviada = False
        st.session_state.fim_ciclo = False
        st.rerun()

# ESTADO 2: EXERCÍCIO EM ANDAMENTO
else:
    # Se não houver exercício carregado na memória, solicita um à API
    if st.session_state.dados_exercicio is None:
        with st.spinner(f"Gerando exercício {st.session_state.num_exercicio} de 5..."):
            
            prompt_geracao = f"""
            Você é um professor de japonês para brasileiros focado na preparação para o JLPT.
            Crie um exercício Cloze em JSON para o nível {nivel} no contexto {contexto}.

            REFERÊNCIAS DE EXERCÍCIOS REAIS DO EXAME (Siga rigorosamente este padrão de estrutura de escrita e simplicidade):
            1. "これは 一つ___(1)___ いくらですか。――― 三百円___(2)___です。" -> Kanjis ocultados: 一つ (ひとつ) / 三百円 (さんびゃくえん)
            2. "わたしの たんじょうびは 五月五日___(1)___です。こどもの 日___(2)___とおなじです。" -> Kanjis ocultados: 五月五日 (ごがついつか) / 日 (ひ)
            3. "バスツアーの お金___(1)___は こんしゅうの 土よう日___(2)___までに はらってください。" -> Kanjis ocultados: お金 (おかね) / 土曜日 (どようび)
            4. "川___(1)___のそばに おおきい さくらの 木___(2)___がありました。" -> Kanjis ocultados: 川 (かわ) / 木 (き)
            5. "ペットボトルの 水___(1)___を 半分___(2)___のみました。" -> Kanjis ocultados: 水 (みず) / 半分 (はんぶん)
            6. "ビルの 上___(1)___から きれいな 月___(2)___ gあみえました。" -> Kanjis ocultados: 上 (うえ) / 月 (つき)
            7. "山下___(1)___さんですね。どうぞ 中___(2)___へ。" -> Kanjis ocultados: 山下 (やました) / 中 (なか)
            8. "あの 木___(1)___の 下___(2)___ deやすみましょう。" -> Kanjis ocultados: 木 (き) / 下 (した)
            9. "あの 女の子___(1)___は テニスが 上手___(2)___ですね。" -> Kanjis ocultados: 女の子 (おんなのこ) / 上手 (じょうず)
            10. "えきの 東口___(1)___で 先生___(2)___に あいました。" -> Kanjis ocultados: 東口 (ひがしぐch) / 先生 (せんsei)

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
            - Apontar de forma super direta onde o estudante brasileiro costuma errar ou se confundir visualmente (ex: diferença de tamanho de traços, semelhanças com letras do nosso alfabeto ou falsos amigos visuais).
            - Fornecer uma dica de memorização mnemônica prática adaptada para a realidade cultural ou linguística do Brasil (ex: trocadilhos fonéticos com o português brasileiro ou comparações com formas físicas de objetos comuns no Brasil).
            - Use LETRAS MAIÚSCULAS apenas para destacar títulos de seção.

            Retorne estritamente neste formato JSON:
            {{
              "texto_pt": "Tradução do texto em português",
              "texto_jp": "Texto em japonês com as marcações ___(1)___ e ___(2)___",
              "alternativas": {{"A": "K1 / K2", "B": "K1 / K2", "C": "K1 / K2", "D": "K1 / K2"}},
              "alternativa_correta": "Letra correspondente",
              "feedback_se_acertou": "PARABÉNS! Os kanjis são [Kanji 1] (leitura / significado) e [Kanji 2] (leitura / significado). No Brasil costumamos confundi-los com [detalhe de confusão de brasileiros]. Para fixar, faça esta associação mental em português: [mnemônico prático voltado para o cotidiano ou cultura do Brasil].",
              "feedback_se_errou": "CORREÇÃO DA ATIVIDADE: A alternativa correta era a [Letra]. Estudantes brasileiros costumam escorregar aqui porque [detalhe de semelhança visual ou fonética que causa confusão no Brasil]. Os kanjis corretos significam [significado] e você pode lembrá-los facilmente pensando que [mnemônico prático em português para brasileiros]."
            }}
            """
            try:
                response = model.generate_content(prompt_geracao)
                st.session_state.dados_exercicio = json.loads(response.text)
            except Exception as e:
                st.error(f"Erro ao conectar com o modelo. Mensagem original: {e}")

    # Exibição do exercício ativo
    if st.session_state.dados_exercicio:
        dados = st.session_state.dados_exercicio
        
        # Cabeçalho indicando o número do exercício
        st.markdown(f"#### **Exercício {st.session_state.num_exercicio} de 5**")
        
        st.info(f"**CONTEXTO EM PORTUGUÊS:**\n\n{dados['texto_pt']}")
        st.markdown("### TEXTO EM JAPONÊS:")
        st.code(dados['texto_jp'], language="text")
        
        st.markdown("### SELECIONE A OPÇÃO CORRETA (Lacuna 1 / Lacuna 2):")
        opcoes = [f"{letra}) {alt}" for letra, alt in dados['alternativas'].items()]
        
        # O seletor de alternativas fica desabilitado após o envio para evitar trapaça ou mudança acidental de voto
        escolha = st.radio("Alternativas:", opcoes, disabled=st.session_state.resposta_enviada)
        
        # Exibe o botão de envio apenas se o aluno ainda não enviou a resposta
        if not st.session_state.resposta_enviada:
            if st.button("Enviar Resposta", type="primary"):
                st.session_state.resposta_enviada = True
                resposta_letra = escolha[0]
                correta = dados['alternativa_correta'].strip().upper()
                
                # Validação pedagógica
                resultado_ok = (resposta_letra == correta)
                if resultado_ok:
                    st.session_state.acertos += 1
                
                # Salva o exercício no histórico que alimentará o dashboard final
                st.session_state.historico.append({
                    "num": st.session_state.num_exercicio,
                    "texto_pt": dados["texto_pt"],
                    "texto_jp": dados["texto_jp"],
                    "escolha": escolha,
                    "correta": correta,
                    "resultado": resultado_ok
                })
                st.rerun()

        # Exibe os resultados e feedbacks após a resposta ser enviada
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
                
            # O botão de avanço surge unicamente na parte inferior pós-feedback
            st.markdown("")
            texto_botao_avanco = "Ver Resultados Finais" if st.session_state.num_exercicio == 5 else "Próximo Exercício"
            
            if st.button(texto_botao_avanco):
                if st.session_state.num_exercicio < 5:
                    st.session_state.num_exercicio += 1
                    st.session_state.resposta_enviada = False
                    st.session_state.dados_exercicio = None  # Reseta para forçar a IA a gerar uma nova pergunta
                    st.rerun()
                else:
                    st.session_state.fim_ciclo = True
                    st.rerun()