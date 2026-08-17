DICIONARIO DE INDICADORES DE BI — PRODUCAO E FITOSSANIDADE

Este documento descreve os indicadores gerenciais expostos pelo modulo
Inteligencia (`app/inteligencia/`) e consumidos pelos dashboards do menu
"BI" > "Produtividade" e "BI" > "Fitossanidade"
(`streamlit/pages/bi/Producao.py`, `streamlit/pages/bi/Fitossanidade.py`,
implementados em `streamlit/components/bi/producao_dashboard.py` e
`streamlit/components/bi/fitossanidade_dashboard.py`, no mesmo padrao dos
demais dashboards de BI do menu — Estoque e Compras). Para cada indicador:
formula de calculo, fonte de dados (tabelas), granularidade, periodicidade
de atualizacao e como interpretar o numero.

Convencao: cada indicador tem uma entrada abaixo. Onde houver campo de
"Endpoint", o dado pode ser consultado ao vivo via API (`GET /inteligencia/...`).

---

## Dashboard: Produtividade (menu BI > Produtividade)

Endpoint: `GET /inteligencia/produtividade?id_safra=&id_talhao=`
Servico: `InteligenciaService.listar_produtividade` (`app/inteligencia/service.py`)
Repositorio: `ProdutividadeRepository.listar` (`app/inteligencia/repository.py`)

### Meta de produtividade (kg/ha)

- **Formula**: valor direto de `planejamento_safra.meta_produtividade`.
- **Fonte**: tabela `planejamento_safra` (modulo Producao), uma linha por
  `(id_talhao, id_safra)`.
- **Granularidade**: por talhao/safra.
- **Periodicidade**: atualizado quando o planejamento da safra e criado ou
  revisado (evento pontual, nao recorrente).
- **Interpretacao**: e o alvo definido no planejamento agronomico da safra.
  Nao existe "bom" ou "ruim" isolado — serve de referencia para o indicador
  de variacao abaixo. Ausencia de meta (`null`) indica talhao sem
  planejamento formal cadastrado para a safra.

### Produtividade realizada (kg/ha)

- **Formula**: `SUM(colheita.quantidade_colhida) / area_referencia`, onde
  `area_referencia = COALESCE(planejamento_safra.area_planejada, talhao.area_hectares)`.
  A soma considera todas as colheitas de todos os plantios vinculados ao
  talhao (um talhao pode ter mais de um plantio/colheita na mesma safra).
- **Fonte**: `colheita` + `plantio` (modulo Producao), agregados por
  `plantio.id_talhao`.
- **Granularidade**: por talhao/safra.
- **Periodicidade**: recalculado a cada consulta (dado ao vivo, nao
  armazenado); reflete o estado mais recente de `colheita` no banco.
- **Interpretacao**: produtividade efetivamente colhida. `null` significa
  que o talhao ainda nao tem colheita registrada na safra (plantio em
  andamento ou pendente) — nao deve ser lido como "zero".

### Variacao percentual (realizado x meta)

- **Formula**: `(produtividade_realizada - meta_produtividade) / meta_produtividade * 100`.
- **Fonte**: derivado dos dois indicadores acima.
- **Granularidade**: por talhao/safra.
- **Periodicidade**: ao vivo, junto com a consulta de produtividade.
- **Interpretacao**:
  - `>= 0%`: talhao atingiu ou superou a meta planejada.
  - `0% a -10%`: leve abaixo da meta; acompanhar, geralmente dentro da
    variabilidade normal de safra (clima, pragas pontuais).
  - `-10% a -20%`: atencao — investigar causa (fitossanidade, irrigacao,
    solo) antes da proxima safra no talhao.
  - `<= -20%`: critico. O dashboard destaca esses talhoes em vermelho na
    tabela ("Talhoes 20% ou mais abaixo da meta"). Priorizar analise de
    solo, historico de ocorrencias fitossanitarias (ver dashboard de
    Fitossanidade) e revisao do plano da proxima safra.
  - `null`: sem meta cadastrada ou sem colheita registrada ainda — nao e
    uma variacao de 0%, e sim dado insuficiente.

### KPIs de resumo (topo do dashboard)

- **Produtividade media realizada**: media simples de `produtividade_realizada`
  entre talhoes com colheita no filtro selecionado.
- **Variacao media vs. meta**: media simples de `variacao_percentual` entre
  talhoes com meta e colheita registradas.
- **Talhoes abaixo da meta**: contagem de talhoes com `variacao_percentual < 0`.
- Uso gerencial: visao rapida da safra/talhao filtrado antes de abrir a
  tabela detalhada.

### Visao geral entre safras (independe do filtro)

- **Formula**: media de `produtividade_realizada` por `id_safra`, sobre
  todos os talhoes retornados por `listar_produtividade()` sem filtro,
  ordenado por `safra.ano`.
- **Fonte**: mesma consulta de produtividade, agregada no cliente
  (`streamlit/components/bi/producao_dashboard.py::_render_visao_geral`),
  sem endpoint dedicado.
- **Granularidade**: por safra (todas as safras com dado, independente do
  filtro de safra/talhao selecionado abaixo).
- **Interpretacao**: mostra se a produtividade media da fazenda esta
  melhorando ou piorando entre safras. So aparece grafico de tendencia a
  partir de 2 safras com colheita registrada — com 1 safra, e exibido um
  aviso em vez de um grafico vazio (nao ha "tendencia" com um unico ponto).

### Custo de defensivos por kg colhido e por hectare (R$/kg, R$/ha)

- **Formula**: `custo_total (fitossanidade) / quantidade_colhida_total` e
  `custo_total / area_hectares`, cruzando os endpoints de produtividade e
  de custo de defensivos pelo mesmo `id_talhao`.
- **Fonte**: `GET /inteligencia/produtividade` + `GET /inteligencia/fitossanidade/custos`,
  unidos no cliente (nenhum dos dois dados sozinho responde "o defensivo
  compensou").
- **Granularidade**: por talhao/safra.
- **Interpretacao**: normaliza o custo — um talhao maior naturalmente gasta
  mais em valor absoluto, mas pode ser mais eficiente em R$/kg ou R$/ha. Um
  R$/kg alto com produtividade baixa no mesmo talhao (visivel no grafico de
  dispersao logo abaixo da tabela) sugere que o gasto com defensivo nao
  esta se traduzindo em colheita — candidato a revisao de manejo.
  `R$/kg` fica em branco quando ainda nao ha colheita registrada.

### Clima x produtividade, por safra

- **Formula**: media de `produtividade_realizada` por safra x precipitacao/
  temperatura media da safra, lidas de `medicao_indicador` (indicadores
  "Precipitacao"/"Temperatura", ja usados pela aba Inteligencia > Clima,
  alimentados via Open-Meteo).
- **Fonte**: `GET /inteligencia/medicoes?id_indicador=...` (indicador
  resolvido por nome via `GET /inteligencia/indicadores`), cruzado com a
  produtividade por safra.
- **Granularidade**: por safra (o clima hoje e registrado por safra, nao
  por talhao — nao ha dado em `condicao_climatica`, tabela por-talhao,
  nesta instalacao).
- **Interpretacao**: correlacao exploratoria, nao causal — util para
  perguntas do tipo "safras com mais chuva renderam mais?". Fica mais
  confiavel a medida que mais safras tiverem clima sincronizado (hoje
  depende de sincronizacao manual em Inteligencia > Clima). Com poucas
  safras, tratar como indicio, nao conclusao.

### Cotacao de mercado da cultura (contexto, sem conversao de unidade)

- **Formula**: nenhuma — leitura direta de `GET /inteligencia/indicadores/cotacao/atual`
  (AgroDoc/CEPEA), casando `cultura.nome` do talhao com o nome do produto
  cotado (ex.: "Soja", "Milho").
- **Interpretacao**: contexto de mercado ao lado da produtividade, para
  apoiar decisao comercial (vender agora x aguardar). **Deliberadamente
  nao multiplicado pela quantidade colhida** — a cotacao vem em R$/saca
  (60kg) ou R$/@ e a quantidade colhida em kg; converter exigiria saber o
  fator exato por cultura, e um valor estimado errado e pior que nenhum
  valor. Culturas sem cotacao correspondente (ex.: Sorgo, Trigo, nesta
  instalacao) simplesmente nao aparecem.

---

## Dashboard: Fitossanidade (menu BI > Fitossanidade)

### Custo de defensivos por talhao/safra

- **Formula**: `SUM(conta_pagar.valor)` para as contas a pagar originadas
  por aplicacoes de defensivo (`conta_pagar.id_aplicacao IS NOT NULL`),
  join `conta_pagar -> aplicacao_defensivo -> controle_fitossanitario ->
  plantio -> talhao`.
- **Fonte**: `conta_pagar` (modulo Financeiro) + `aplicacao_defensivo` +
  `controle_fitossanitario` (modulo Fitossanidade). O valor ja e o custo
  realizado (`preco do insumo x volume aplicado`), calculado no momento do
  registro da aplicacao (`FitossanidadeService._notify_financial_cost`) —
  o dashboard nao recalcula, apenas soma o que ja foi lancado no financeiro.
- **Granularidade**: por talhao/safra.
- **Periodicidade**: ao vivo; reflete todas as aplicacoes registradas ate o
  momento da consulta (nao ha corte por data, o filtro e apenas por safra).
- **Interpretacao**: custo direto de insumos fitossanitarios por talhao.
  Compare entre talhoes da mesma cultura/safra para identificar
  discrepancias (ex.: talhao com custo muito acima da media pode indicar
  pressao de pragas mais alta ou dose de aplicacao excessiva). Talhoes com
  `custo_total = 0` e `total_aplicacoes = 0` nao tiveram nenhum controle
  fitossanitario registrado no periodo — pode ser positivo (baixa
  incidencia) ou indicar falta de monitoramento; cruzar com o indicador de
  ocorrencias abaixo antes de concluir.
- **Endpoint**: `GET /inteligencia/fitossanidade/custos?id_safra=&id_talhao=`

Endpoint: `GET /inteligencia/fitossanidade/custos?id_safra=&id_talhao=`
Servico: `InteligenciaService.listar_custos_fitossanidade`
Repositorio: `FitossanidadeBiRepository.custos_por_talhao`

### Ocorrencias de agentes nocivos por severidade

- **Formula**: `COUNT(ocorrencia_agente.id_ocorrencia)` agrupado por
  `(talhao, safra, controle_fitossanitario.nivel_severidade, agente_nocivo.nome_comum)`.
  A severidade usada e a do controle fitossanitario associado (escala
  compartilhada: Baixo < Medio < Alto < Critico —
  `app/fitossanidade/enum.py::SeverityLevel`).
- **Fonte**: `ocorrencia_agente` + `controle_fitossanitario` +
  `agente_nocivo` + `plantio` + `talhao` (modulo Fitossanidade/Producao).
- **Granularidade**: por talhao/safra/severidade/agente.
- **Periodicidade**: ao vivo; so aparecem talhoes com pelo menos uma
  ocorrencia registrada no filtro (talhoes sem ocorrencia nao aparecem
  na lista, ao contrario do dashboard de custo).
- **Interpretacao**: concentracao de ocorrencias em severidade Critico/Alto
  no mesmo talhao indica foco ativo de praga/doenca que pode justificar
  produtividade abaixo da meta (cruzar com o dashboard de Produtividade) e
  custo elevado de defensivos. Recorrencia do mesmo agente em varias safras
  no mesmo talhao sugere rotacao de cultura ou manejo de solo, nao apenas
  controle quimico pontual.
- **Endpoint**: `GET /inteligencia/fitossanidade/ocorrencias?id_safra=&id_talhao=`

Endpoint: `GET /inteligencia/fitossanidade/ocorrencias?id_safra=&id_talhao=`
Servico: `InteligenciaService.listar_ocorrencias_fitossanidade`
Repositorio: `FitossanidadeBiRepository.ocorrencias_por_severidade`

### KPIs de resumo (topo do dashboard)

- **Custo total de defensivos**: soma de `custo_total` no filtro selecionado.
- **Aplicacoes registradas**: soma de `total_aplicacoes`.
- **Talhoes com custo no periodo**: contagem de talhoes com `custo_total > 0`.
- **Ocorrencias registradas**: soma de `total_ocorrencias`.
- **Severidade critica / alta**: soma de ocorrencias com
  `nivel_severidade = 'Critico'` / `'Alto'` — leitura rapida do nivel de
  risco fitossanitario do periodo antes de abrir o detalhe por talhao.

### Visao geral entre safras (independe do filtro)

- **Formula**: soma de `custo_total` por safra (linha) e soma de
  `total_ocorrencias` por safra/severidade (barras empilhadas), sobre todos
  os talhoes, sem filtro.
- **Fonte**: mesmos dois endpoints de custo/ocorrencias, agregados no
  cliente (`streamlit/components/bi/fitossanidade_dashboard.py::_render_visao_geral`).
- **Interpretacao**: mostra se o custo com defensivos e a pressao
  fitossanitaria estao subindo ou caindo entre safras — sinal de tendencia
  estrutural (ex.: agente resistente, area precisando de rotacao) versus
  problema pontual de uma safra. Assim como no dashboard de Produtividade,
  precisa de pelo menos 2 safras com dado para exibir a tendencia.

### Custo de defensivos por hectare (R$/ha)

- **Formula**: `custo_total / talhao.area_hectares` (area lida do endpoint
  de produtividade, cruzada por `id_talhao`).
- **Interpretacao**: normaliza o custo pelo tamanho do talhao — permite
  comparar talhoes de areas diferentes sem que o maior pareca sempre "mais
  caro" so por ser maior.

### Top agentes ofensores

- **Formula**: `SUM(total_ocorrencias)` agrupado por `agente_nome`, sobre o
  filtro selecionado, top 10.
- **Interpretacao**: ranking de pragas/doencas mais recorrentes no recorte
  atual — direciona onde priorizar controle preventivo ou revisao de
  defensivo/dose na proxima aplicacao.

### Pressao fitossanitaria x variacao de produtividade

- **Formula**: por talhao, soma de ocorrencias com severidade Alto ou
  Critico (eixo X) x `variacao_percentual` de produtividade do mesmo talhao
  (eixo Y, do dashboard de Produtividade).
- **Fonte**: `GET /inteligencia/fitossanidade/ocorrencias` +
  `GET /inteligencia/produtividade`, cruzados por `id_talhao`.
- **Granularidade**: por talhao/safra.
- **Interpretacao**: e o cruzamento mais direto entre os dois dashboards —
  talhoes no canto inferior-direito (muitas ocorrencias graves, variacao
  bem negativa) sao os candidatos mais fortes a "a fitossanidade explica a
  queda de produtividade aqui". Talhoes com muitas ocorrencias mas
  variacao proxima de zero sugerem que o controle aplicado funcionou.
  Correlacao, nao prova de causalidade — cruzar com o historico de
  aplicacoes (dose, timing) antes de decidir.

---

## Limitacoes conhecidas (para leitura correta dos numeros)

- `talhao.id_safra` e fixo por linha (cada talhao pertence a exatamente uma
  safra no modelo de dados) — nao ha ambiguidade de "talhao replantado em
  outra safra" nos indicadores acima.
- O custo de defensivos soma `conta_pagar.valor` independente do status da
  conta (`ABERTA`, `PAGA`, etc.) — o indicador mede custo incorrido, nao
  caixa desembolsado. Para fluxo de caixa, usar o dashboard financeiro
  (`streamlit/components/financeiro/intelligence.py`).
- Custo de insumos de adubacao/irrigacao nao entra neste indicador (apenas
  aplicacoes de defensivo, `aplicacao_defensivo`), pois e o unico fluxo do
  sistema com custo persistido de forma automatica hoje.
