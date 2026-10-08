-- Banco de itens do TCC: Cloze de dois kanjis com feedback por LLM.
-- SQLite. Roda uma vez: sqlite3 banco.db < schema.sql

-- um item = um exercício Cloze pronto pra usar no app (só entra aqui depois
-- de passar pelo validador). cada linha é uma questão do banco
CREATE TABLE IF NOT EXISTS itens (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nivel_jlpt      TEXT NOT NULL,              -- N5, N4, N3, N2, N1
    contexto        TEXT,                       -- Cotidiano, Restaurante, ...
    texto_pt        TEXT NOT NULL,
    texto_jp        TEXT NOT NULL,              -- com ___(1)___ e ___(2)___
    kanji1          TEXT NOT NULL,
    kanji2          TEXT NOT NULL,
    alternativa_a   TEXT NOT NULL,
    alternativa_b   TEXT NOT NULL,
    alternativa_c   TEXT NOT NULL,
    alternativa_d   TEXT NOT NULL,
    alternativa_correta TEXT NOT NULL,          -- "A" | "B" | "C" | "D"
    feedback_acertou    TEXT,
    feedback_errou      TEXT,
    origem          TEXT NOT NULL DEFAULT 'llm', -- 'llm' | 'llm_editado' | 'manual'
    log_id          INTEGER,                     -- id em geracoes que originou este item
    criado_em       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (log_id) REFERENCES geracoes(id)
);

-- toda tentativa de geração (aprovada ou não) fica registrada aqui, com o
-- prompt exato, a resposta crua da API e o veredito do validador. é essa
-- tabela que sustenta qualquer número que eu citar no TCC tipo "12% dos
-- itens de N5 foram reprovados por kanji fora da lista" - dá pra rastrear
-- até o caso concreto
CREATE TABLE IF NOT EXISTS geracoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nivel_jlpt      TEXT NOT NULL,
    contexto        TEXT,
    prompt_enviado  TEXT NOT NULL,
    resposta_bruta  TEXT NOT NULL,               -- JSON cru devolvido pelo Gemini
    aprovado        INTEGER NOT NULL,            -- 0 ou 1
    regra_violada   TEXT,                        -- nome da regra, se reprovado (NULL se aprovado)
    detalhe_violacao TEXT,                       -- o que especificamente falhou
    modelo          TEXT NOT NULL DEFAULT 'gemini-2.5-flash',
    criado_em       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_geracoes_nivel ON geracoes(nivel_jlpt);
CREATE INDEX IF NOT EXISTS idx_geracoes_aprovado ON geracoes(aprovado);
CREATE INDEX IF NOT EXISTS idx_itens_nivel ON itens(nivel_jlpt);
