from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.comercial.enum import StatusCliente, UnitSymbol
from app.core.enum import StatusCertificacao
from app.estoque.enum import StatusLote


# Categoria do catalogo de produtos comerciais
class CategoriaProdutoModel(BaseModel):
    id_categoria: int
    nome: str


# Unidade de medida usada pelos produtos (kg, litro, saca, etc.)
class UnidadeMedidaModel(BaseModel):
    id_unidade: int
    sigla: UnitSymbol
    descricao: str


# Produto do catalogo comercial (insumo, grao, produto acabado etc.)
class ProdutoModel(BaseModel):
    id_produto: int
    id_categoria: int
    id_unidade: int
    nome: str
    tipo: str | None = None
    preco: Decimal | None = None


# Dados comerciais complementares de um produto (extensao 1:1 de produto)
class ProdutoComercialModel(BaseModel):
    id_produto: int
    codigo_comercial: str | None = None
    marca: str | None = None
    descricao_comercial: str | None = None


# Atributos especificos de um produto do tipo grao (extensao 1:1 de produto)
class GraoModel(BaseModel):
    id_produto: int
    umidade_maxima: Decimal | None = None
    impureza_maxima: Decimal | None = None
    classificacao_tipo: str | None = None


# Cotacao de mercado de um produto do tipo grao em uma data
class CotacaoGraoModel(BaseModel):
    id_cotacao: int
    id_produto: int
    data_cotacao: date
    preco: Decimal


# Atributos especificos de um produto do tipo insumo agricola (extensao 1:1 de produto)
class InsumoModel(BaseModel):
    id_produto: int
    classe_agronomica: str | None = None
    principio_ativo: str | None = None
    periodo_carencia_dias: int | None = None
    registro_mapa: str | None = None


# Tipo de certificacao (organico, rainforest alliance etc.)
class CertificacaoModel(BaseModel):
    id_certificacao: int
    nome: str
    orgao_emissor: str | None = None
    tipo: str | None = None


# Vinculo de uma certificacao a uma fazenda, com vigencia e numero do certificado
class CertificacaoFazendaModel(BaseModel):
    id_cert_fazenda: int
    id_certificacao: int
    id_fazenda: int
    dt_emissao: date | None = None
    dt_validade: date | None = None
    numero_certificado: str | None = None
    status: StatusCertificacao


# Cliente (comprador) do modulo comercial
class ClienteModel(BaseModel):
    id_cliente: int
    id_pessoa: int
    status: StatusCliente
    pessoa_nome: str | None = None


# Venda realizada a um cliente
class VendaModel(BaseModel):
    id_venda: int
    id_cliente: int
    id_centro_custo: int
    valor_total: Decimal
    data_venda: date | None = None


# Item (linha) de uma venda
class ItemVendaModel(BaseModel):
    id_item_venda: int
    id_venda: int
    id_produto: int
    id_lote: int | None = None
    quantidade: Decimal
    valor_unitario: Decimal


# ----------------------------------------------------------------------
# Contratos de entrada da API (sem id, preenchido pelo banco na criacao)
# ----------------------------------------------------------------------
class NovaCategoriaProduto(BaseModel):
    nome: str


class NovoCentroCusto(BaseModel):
    nome: str


class NovaUnidadeMedida(BaseModel):
    sigla: UnitSymbol
    descricao: str


class NovoProduto(BaseModel):
    id_categoria: int
    id_unidade: int
    nome: str
    tipo: str | None = None
    preco: Decimal | None = None


class NovoProdutoComercial(BaseModel):
    id_produto: int
    codigo_comercial: str | None = None
    marca: str | None = None
    descricao_comercial: str | None = None


class NovoGrao(BaseModel):
    id_produto: int
    umidade_maxima: Decimal | None = None
    impureza_maxima: Decimal | None = None
    classificacao_tipo: str | None = None


class NovaCotacaoGrao(BaseModel):
    id_produto: int
    data_cotacao: date
    preco: Decimal


class NovoInsumo(BaseModel):
    id_produto: int
    classe_agronomica: str | None = None
    principio_ativo: str | None = None
    periodo_carencia_dias: int | None = None
    registro_mapa: str | None = None


class NovaCertificacao(BaseModel):
    nome: str
    orgao_emissor: str | None = None
    tipo: str | None = None


class NovaCertificacaoFazenda(BaseModel):
    id_certificacao: int
    id_fazenda: int
    status: StatusCertificacao
    dt_emissao: date | None = None
    dt_validade: date | None = None
    numero_certificado: str | None = None


class NovoCliente(BaseModel):
    nome: str
    documento: str
    status: StatusCliente = StatusCliente.ATIVO


# Item informado ao registrar uma venda: id_estoque nao e persistido em
# item_venda, e usado apenas para saber de onde dar baixa no Estoque.
class ItemVendaEntrada(BaseModel):
    id_produto: int
    id_estoque: int
    id_lote: int | None = None
    quantidade: Decimal
    valor_unitario: Decimal


class NovaVenda(BaseModel):
    id_cliente: int
    id_centro_custo: int
    data_venda: date | None = None
    itens: list[ItemVendaEntrada]


# Venda com os itens ja carregados (resposta de leitura)
class VendaComItens(VendaModel):
    itens: list[ItemVendaModel] = []


# ----------------------------------------------------------------------
# Leituras auxiliares de outros dominios (lote pertence ao Estoque) e
# opcoes para preencher selects no frontend
# ----------------------------------------------------------------------
class LoteInfo(BaseModel):
    id_lote: int
    id_produto: int
    codigo_lote: str
    status: StatusLote


class ProdutoOption(BaseModel):
    id_produto: int
    nome: str


class ClienteOption(BaseModel):
    id_cliente: int
    nome: str


class CentroCustoOption(BaseModel):
    id_centro_custo: int
    nome: str


class LoteOption(BaseModel):
    id_lote: int
    codigo_lote: str
    produto_nome: str | None = None
    status: StatusLote
