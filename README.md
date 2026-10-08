# Tutor de Kanji com IA

Protótipo desenvolvido como parte de um Trabalho de Conclusão de Curso (Ciências Exatas — UFJF, opção de segundo ciclo em Engenharia Computacional). O app gera exercícios do tipo Cloze com duas lacunas de Kanji, adaptados ao nível JLPT escolhido, usando a API do Gemini para gerar o item e o feedback pedagógico. Os itens gerados passam por uma validação automática por regras (lista de Kanjis permitidos por nível, restrição a kana em N5/N4, unicidade da alternativa correta), usada para medir a taxa de inconsistência da IA.

## Estrutura do repositório

- **`app.py`** — app Streamlit principal, com a interface do exercício.
- **`banco_de_questoes/`** — scripts usados para montar e validar o banco de itens reportado nos resultados do TCC:
  - `gerador_banco.py` — gera itens via Gemini e salva no banco (`banco.db`)
  - `validador.py` — validação por regras (usado tanto na geração quanto na revalidação)
  - `revalidar.py` — reaplica o validador atual sobre itens já salvos, sem gastar chamada nova de API
  - `inspecionar_lacunas.py` — diagnóstico de reprovações pela regra de lacunas
  - `exportar_para_forms.py` — exporta os itens aprovados para o formato usado no Google Forms
  - `kanji_niveis/` — listas oficiais de Kanji por nível JLPT
- **`prototipos/`** — versões anteriores/experimentais do app, mantidas como histórico do desenvolvimento.
