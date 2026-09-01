DICIONARIO DE INDICADORES DE BI — PRODUCAO, FITOSSANIDADE, COMERCIAL, FINANCEIRO, LOGISTICA, MANUTENCAO E MARGEM

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

## Resumo dos indicadores comerciais, financeiros, logísticos e de manutenção

- **IND-10** — Custo de frete por operação/safra — Logística — R$
- **IND-11** — Tempo médio entre despacho e entrega — Logística — horas
- **IND-12** — Receita total e por cliente — Comercial — R$
- **IND-13** — Ticket médio de venda — Comercial — R$
- **IND-14** — Vendas por produto/safra — Comercial — R$ / qtd.
- **IND-15** — Fluxo de caixa consolidado — Financeiro — R$
- **IND-16** — Aging de contas a pagar/receber — Financeiro — R$ / dias
- **IND-17** — Custo de manutenção por máquina/período — Manutenção — R$
- **IND-18** — Proporção preventiva x corretiva — Manutenção — %
- **IND-19** — Margem por safra — Margem por Safra — R$ / %

## Dashboard: Logística (menu BI > Logistica)

### IND-10 — Custo de frete por operação/safra

- **Formula**: soma dos `custo_previsto` das operações de logística, agregada por operação e por safra; no dashboard, o KPI principal e o total de `df["Custo frete"].sum()` e o custo medio por operacao e `total_frete / total_operacoes`.
- **Fonte**: `LogisticsClient.list_operations()`, `list_all_loads()`, lotes e `producao_api.listar("/safras")`, com alocacao pela safra vinculada aos lotes envolvidos na carga/operacao.
- **Granularidade**: por operação e por safra no filtro/agrupamento do dashboard.
- **Periodicidade**: atualiza ao consultar o dashboard (dados ao vivo), com filtro de periodo e safra no cliente.
- **Interpretacao**: mostra o custo logístico efetivo de movimentacao do produto. Operacoes com custo alto no mesmo periodo devem ser comparadas por safra e por origem/destino para distinguir efeito de distancia, volume ou atraso de entrega.
- **Dashboard**: `streamlit/components/bi/logistica_dashboard.py`

### IND-11 — Tempo médio entre despacho e entrega

- **Formula**: media de `(data_entrega - data_saida)` em horas para cada despacho registrado, calculada como `sum(duracoes) / len(duracoes)`; o dashboard exibe `df["Tempo desp/entrega (h)"].mean()`.
- **Fonte**: registros de despacho/entrega da API de logística (`_fetch_dispatch(operation_id, load_id)`), com `data_saida` e `data_entrega` por carga.
- **Granularidade**: por operacao, consolidado no periodo filtrado.
- **Periodicidade**: ao vivo, por consulta do dashboard.
- **Interpretacao**: mede a velocidade operacional da entrega. Valores crescentes e persistentes indicam gargalos em transporte, documentacao, portaria, conferencias ou capacidade da frota.

## Dashboard: Comercial (menu BI > Comercial)

### IND-12 — Receita total e por cliente

- **Formula**: `receita_total = SUM(quantidade * valor_unitario)` sobre todos os itens de venda; por cliente, `df.groupby("Cliente").agg({"Valor": "sum"})`.
- **Fonte**: `ComercialClient.list_vendas()` e fallback de detalhes por venda (`get_venda`) quando a listagem nao inclui `itens`. Cada linha e um item de venda, com produto, quantidade, valor unitario e safra associada.
- **Granularidade**: total da base filtrada e por cliente; também suporta filtro por safra, produto e periodo.
- **Periodicidade**: ao vivo quando o BI e carregado; filtros por periodo/safra produto/cliente aplicados no cliente.
- **Interpretacao**: indica a performance comercial em valor bruto e a concentracao de receita por cliente. Clientes com grande peso no total exigem acompanhamento de mix, cobranca e renovacao de carteira.
- **Dashboard**: `streamlit/components/bi/comercial_dashboard.py`

### IND-13 — Ticket médio de venda

- **Formula**: `ticket_medio = receita_total / numero_de_vendas`; no codigo, `n_vendas = df["IdVenda"].nunique()`.
- **Fonte**: mesma base de itens de venda do dashboard comercial, convertida para valor por item e consolidada por venda.
- **Granularidade**: por periodo/safra/cliente/produto selecionado.
- **Periodicidade**: ao vivo no carregamento do dashboard.
- **Interpretacao**: mede o valor medio por venda. Tendencias de queda podem indicar reducao do mix premium, menor volume por pedido, ou perda de oportunidade em negocios de maior ticket.

### IND-14 — Vendas por produto/safra

- **Formula**: `valor_por_produto = SUM(quantidade * valor_unitario)` agrupado por `Produto`; no mesmo dashboard, a visão por safra usa `groupby([pd.Grouper(key="Data", freq="ME"), "Safra"]).agg({"Valor": "sum"})` para a linha de tendencia de receita por safra.
- **Fonte**: `itens` das vendas (produto, quantidade, valor unitario, data da venda e safra atribuida por data ou lote).
- **Granularidade**: por produto, por safra e no tempo (mensal). A quantidade vendida tambem e exibida em `Quantidade` por produto.
- **Periodicidade**: ao vivo, com filtro por periodo, safra e cliente.
- **Interpretacao**: ajuda a identificar mix comercial, volume e concentracao por cultura/produto. Indica se a receita vem de poucos produtos ou de um mix mais diversificado.

## Dashboard: Financeiro (menu BI > Financeiro)

### IND-15 — Fluxo de caixa consolidado

- **Formula**: somatorio de movimentacoes de caixa por dia, tratadas como `Entradas` quando `id_conta_receber` e `Saidas` quando `id_conta_pagar`; no grafico, cada linha e agregada por `data` e `tipo` e o valor e somado em `df.groupby(["data", "tipo"]).sum()`.
- **Fonte**: `FinanceiroClient.list_fluxo_por_periodo(data_inicio, data_fim)`, carregando movimentos financeiros vinculados a contas a pagar e receber.
- **Granularidade**: por data e tipo de movimento (entradas/saidas), com consolidação do periodo filtrado.
- **Periodicidade**: configurada pelo filtro de data do dashboard (padrao: ultimo 90 dias se nao houver selecao).
- **Interpretacao**: mostra a liquidez operacional do negocio em periodo, mostrando se as entradas cobrem as saidas e em que momentos o caixa se fortalece ou aperta. E importante para planejamento de pagamento, investimento e cobertura de capital de giro.
- **Dashboard**: `streamlit/components/bi/financeiro_dashboard.py` e helper `streamlit/components/financeiro/intelligence.py`

### IND-16 — Aging de contas a pagar/receber

- **Formula**: para cada conta em aberto, calcula bucket de vencimento em relacao a hoje: `Vencidas`, `Até 7 dias`, `8–15 dias`, `16–30 dias`, `Mais de 30 dias`; depois soma `saldo` por bucket e tipo (`A pagar` / `A receber`).
- **Fonte**: listas de `contas_pagar` e `contas_receber` com status em aberto (`ABERTA`, `PARCIALMENTE_PAGA`, `VENCIDA`, etc.) e campo `vencimento`/`saldo`.
- **Granularidade**: por bucket de vencimento e tipo de conta; tabela critica detalha dias em atraso e saldo.
- **Periodicidade**: em tempo real no carregamento, com dependencia da data de hoje.
- **Interpretacao**: ajuda a priorizar cobrancas e pagamentos e identificar risco de liquidez. O destaque de contas vencidas sinaliza necessidade de acao imediata para evitar atrasos ou perda de relacionamento com fornecedores e clientes.

## Dashboard: Manutenção (menu BI > Manutenção)

### IND-17 — Custo de manutenção por máquina/período

- **Formula**: soma de `custo` das manutencoes concluídas (`status == "CONCLUIDA"`) no periodo e maquina selecionados, agrupado por `Maquina`: `df_man.groupby("Maquina").agg({"Custo": "sum"})`.
- **Fonte**: `manutencao_api.list_manutencoes_preventivas()`, `list_manutencoes_corretivas()`, `list_ordens_servico()` e `list_maquinas()`; o custo e lido do campo `manutencao.custo`.
- **Granularidade**: por máquina e periodo do filtro; acrescenta detalhe de tipo (preventiva/corretiva).
- **Periodicidade**: ao vivo, filtrado por periodo de data (`render_filter_bar`) e opcao de maquina.
- **Interpretacao**: identifica onde o custo de manutenção esta mais concentrado. Maquinas com alto custo em corretivas podem indicar falta de previsibilidade, desgaste acelerado ou necessidade de planejamento de inspeccao preventiva.
- **Dashboard**: `streamlit/components/bi/manutencao_dashboard.py`

### IND-18 — Proporção preventiva x corretiva

- **Formula**: calculada por custo, nao por quantidade de ocorrencias: `preventiva_pct = preventivo_custo / (preventivo_custo + corretivo_custo) * 100` e `corretiva_pct = corretivo_custo / (preventivo_custo + corretivo_custo) * 100`.
- **Fonte**: mesma base de manutencoes concluídas do indicador anterior, separada por tipo (`Preventiva` vs `Corretiva`).
- **Granularidade**: proporcao do custo total de manutenção no periodo/maquina filtrado.
- **Periodicidade**: ao vivo, conforme filtros.
- **Interpretacao**: quanto maior a quota preventiva, melhor o perfil de manutencao de um parque. Dominio de corretivas a longo prazo tende a elevar custo, paralisaçoes e perdas de produtividade.

## Dashboard: Margem por safra (menu BI > Margem)

### IND-19 — Margem por safra

- **Formula (valor)**: `margem = receita_total - custo_insumos - custo_logistica - custo_manutencao`, onde:
  - `receita_total = SUM(quantidade * valor_unitario)` dos itens de venda;
  - `custo_insumos = soma das compras` na safra;
  - `custo_logistica = soma dos custos previstos das operacoes de transporte` 
    atribuidos a safra;
  - `custo_manutencao = soma dos custos de manutencao concluida` na safra.
- **Formula (percentual)**: `margem_percentual = (margem / receita_total) * 100`, quando `receita_total > 0`.
- **Fonte**: cruzamento de dados de vendas (`ComercialClient`), compras (`PurchasesClient`), logística (`LogisticsClient`) e manutenção (`manutencao_client`), atribuidos a safra por data do evento ou pelo lote/vinculo da operação.
- **Granularidade**: por safra e por periodo selecionado; o dashboard tambem mostra a soma total e a tabela detalhada por safra.
- **Periodicidade**: conforme filtro de periodo e data e atualizacao ao vivo do dashboard.
- **Interpretacao**: e o indicador financeiro mais direto para comparar a rentabilidade por safra. Margens positivas e crescentes indicam que o mix e o custo operacional estao sendo sustentados; margens negativas, mesmo que temporarias, exigem revisão de precificacao, mix de produtos, compras, logistica e manutenção.
- **Premissas e limitacoes**: o dashboard e intencionalmente conservador e usa atribuicao direta por data/lote quando houver correspondencia; quando existe multipla safra em uma mesma operacao ou evento, a alocacao e aproximada pela regra de safra aplicada, sem rateio complexo entre safras.
- **Dashboard**: `streamlit/components/bi/margem_dashboard.py`

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
