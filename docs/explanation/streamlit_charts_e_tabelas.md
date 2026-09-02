SISTEMA DE GRAFICOS E TABELAS DO STREAMLIT (BI E TELAS DE CADASTRO)

Este documento descreve a camada de apresentacao usada por todos os
dashboards de BI (`streamlit/components/bi/`) e pelas telas de cadastro
(`streamlit/pages/*.py` + `streamlit/components/<modulo>/*_tables.py`):
qual biblioteca cada peca usa, os modulos compartilhados, as convencoes
de formatacao e um problema conhecido do Streamlit que todo novo codigo
nessa camada precisa levar em conta.

---

## Bibliotecas

- **Graficos**: Altair/Vega-Lite nativo do Streamlit (`st.altair_chart`).
  Nao ha mais Plotly no projeto — foi removido de `requirements.txt`.
- **Tabelas**: `st.dataframe` nativo com `column_config`. Nao ha mais
  `streamlit-aggrid` (AgGrid) — tambem removido de `requirements.txt`.

Ambas as trocas foram feitas para herdar automaticamente o tema definido
em `.streamlit/config.toml` (`chartCategoricalColors`,
`chartSequentialColors`, cores semanticas, bordas, fonte) e para ficar
consistente com as boas praticas atuais do Streamlit (ver skill
`developing-with-streamlit`), em vez de depender de um componente de
terceiros com tema proprio.

---

## Tema (`.streamlit/config.toml`)

Fonte unica da identidade visual: paleta categorica/sequencial dos
graficos, cores semanticas (`greenColor`, `redColor`, `orangeColor`,
`blueColor`, `grayColor`) usadas pelos badges e por `ProgressColumn`,
tipografia (Inter) e raio de borda. Alterar cor de marca, cor de grafico
ou cor de status comeca e termina aqui — os modulos abaixo apenas leem
esses tokens, nao redefinem cor em nenhum lugar.

---

## `components/bi/charts.py` — graficos de BI

Modulo unico para todos os graficos de dashboard. Nao criar grafico
Altair "cru" dentro de um `*_dashboard.py`; adicionar/estender uma
funcao aqui.

- `bar_chart`, `line_chart`, `scatter_chart`: encapsulam eixo, tooltip,
  ordenacao categorica, cores (com ou sem `color_map` explicito) e o
  contrato de clique-para-filtrar (ver abaixo). Rotulos de eixo
  categoricos usam `labelOverlap="greedy"` e `labelLimit` para nao
  sobrepor quando ha muitas categorias — nao remover isso, ja foi causa
  de eixo ilegivel em telas com 10+ categorias (ex.: Fitossanidade por
  talhao).
- `donut_chart`: substituto do antigo grafico de pizza Plotly
  (ex.: preventiva x corretiva em Manutencao).
- `sankey_chart`: diagrama de fluxo (origem -> destino) construido do
  zero com `mark_area`/`mark_rect`/`mark_text` em camadas, ja que
  Vega-Lite nao tem um mark de Sankey nativo. Cada link e desenhado como
  uma camada `alt.Chart` independente (uma por linha do `df`) em vez de
  um unico chart agrupado por `detail` — testamos a versao agrupada e o
  Vega-Lite nao desenha a area corretamente quando varias faixas se
  sobrepoem no mesmo intervalo de X (fica com paths de largura zero,
  fluxo invisivel). Se for alterar essa funcao, valide visualmente com
  um fluxo real de 8+ nos, nao so com 2-3 nos.
- `log_y=True` em `bar_chart`: `mark_bar` sempre ancora no `y=0`, que e
  indefinido em escala log — toda barra fica com altura zero e some sem
  erro nenhum. A funcao filtra valores `<= 0` e troca `mark_bar` por
  `mark_point` (nao ha baseline para um ponto quebrar). Nao voltar a usar
  `mark_bar` com escala log sem resolver esse problema de novo.

### Contrato de clique-para-filtrar

Quando `select_key` e passado, o clique e normalizado e gravado em
`st.session_state[select_key]` no formato
`{"selection": {"points": [{"x": ..., "legendgroup": ..., <campo>: ...}]}}`,
o mesmo formato que `components/bi/filters.py::apply_bar_click` e
`apply_month_click` ja esperavam da implementacao anterior em Plotly.
Isso foi proposital para nao precisar alterar `filters.py`: o grafico
sempre usa `alt.selection_point(name="points", ...)` e depois copia o
valor do campo real (`x_field`, `color_field`) para as chaves `x` /
`legendgroup` que o filtro le.

---

## `components/shared/palette.py` — badges e cores semanticas

- `semantic(tone)` / `semantic_bg(tone)`: hex da cor semantica atual
  (`"green"`, `"red"`, `"orange"`, `"blue"`, `"gray"`), ja resolvendo
  claro/escuro via `is_dark_theme()`.
- `badge_column(label, options, tones, **kwargs)` + `badge_value(label)`:
  par de funcoes para status/tipo em tabela. `badge_value` embrulha o
  rotulo numa lista de um item (`["Liberado"]`); `badge_column` monta um
  `st.column_config.MultiselectColumn(disabled=True, ...)` cuja cor de
  cada opcao vem do dicionario `tones`. Essa e a forma padrao de exibir
  status colorido em qualquer tabela do projeto — e o unico jeito de um
  `st.dataframe` pintar uma celula sem CSS custom (MarkdownColumn so
  renderiza cor num overlay ao clicar, nao na celula).
- `status_dot(tone)`: emoji de bolinha colorida, usado apenas como texto
  solto (ex.: dentro de uma frase em `st.caption`), nao em tabela — para
  tabela, usar sempre `badge_column`/`badge_value`.

---

## `components/shared/formatters.py` — formatacao segura para nulo

`format_money_or_dash`, `format_number_or_dash`, `format_int_or_dash`.

**Por que existem**: nesta versao do Streamlit, `st.column_config.NumberColumn`
renderiza um valor nulo/ausente como o texto literal `"None"` na celula,
nao como celula em branco — isso vale para qualquer `format` (padrao,
`"localized"`, `"%.2f"`, `"%d"` etc.), entao trocar o formato nao
resolve. Confirmado isolando o caso numa pagina de teste com
`pd.DataFrame({"a": [1.0, None, 2.5]})`.

Regra pratica: **toda coluna numerica que pode legitimamente nao ter
valor (sem colheita ainda, sem safra vinculada, sem capacidade
cadastrada, etc.) deve ser formatada como texto** com uma dessas
funcoes e exibida com `st.column_config.TextColumn(alignment="right")`,
nunca com `NumberColumn` direto sobre uma coluna com `None`/`NaN`. Uma
coluna numerica só pode ficar como `NumberColumn` quando o dado de
origem garante que ela nunca é nula.

Essa troca foi aplicada nas tabelas mais visitadas (Produtividade,
Logistica, saldo de Pagamento/Recebimento/Fluxo de caixa, preco de
Produto, capacidade de Local de estoque), mas o problema é do
componente do Streamlit, não do dado — qualquer coluna nova com valor
opcional deve nascer já usando esse padrão.

---

## Tabelas de cadastro (`components/shared/screens.py::data_table`)

Ponto unico usado por toda tela CRUD (Comercial, Compras, Estoque,
Financeiro, Fitossanidade, Logistica, Manutencao): `st.dataframe` com
selecao de linha nativa (`on_select="rerun"`, `selection_mode="single-row"`),
sem AgGrid. Aceita `column_config` opcional — cada `*_tables.py` do
modulo expoe uma funcao `*_column_config()` ao lado do `*_df()` que
monta o DataFrame, e a pagina passa os dois juntos para `data_table`.

Convencao por `*_tables.py` novo:
- Datas: manter como objeto `date`/`datetime` no DataFrame (nao formatar
  como string) e usar `st.column_config.DateColumn`/`DatetimeColumn`.
- Dinheiro/quantidade sem nulos possiveis: `NumberColumn(format="localized")`
  (agrupamento de milhar no locale do navegador; nao usar `format="R$ %,.2f"`,
  que forca separador americano).
- Dinheiro/quantidade com nulo possivel: ver secao anterior
  (`format_money_or_dash`/`format_number_or_dash` + `TextColumn`).
- Status/tipo: `badge_column`/`badge_value` (secao anterior).
- Coluna identificadora (ID, nome, codigo): `pinned=True` na primeira
  coluna relevante para nao perder o contexto ao rolar a tabela para o
  lado.
