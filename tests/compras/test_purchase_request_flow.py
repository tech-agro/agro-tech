"""Unit tests for purchase request, quotation, invoice and equipment flow."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.compras.enum import (
    OrderStatus,
    PurchaseRequestStatus,
    PurchaseType,
    QuotationStatus,
)
from app.compras.models.order import OrderModel
from app.compras.models.purchase_request import PurchaseRequestModel
from app.compras.models.purchase_request_item import PurchaseRequestItemModel
from app.compras.models.quotation_item import QuotationItemModel
from app.compras.models.supplier_quotation import SupplierQuotationModel
from app.compras.models.equipment_purchase_detail import EquipmentPurchaseDetailModel
from app.compras.schemas.purchase_invoice import PurchaseInvoiceCreateSchema
from app.compras.schemas.purchase_request import (
    ConvertRequestToOrderSchema,
    PurchaseRequestCreateSchema,
)
from app.compras.schemas.purchase_request_item import PurchaseRequestItemCreateSchema
from app.compras.service import PurchaseService


def _service(**repos) -> PurchaseService:
    return PurchaseService(**repos)


def test_create_request_does_not_create_order():
    request_repo = MagicMock()
    request_item_repo = MagicMock()
    order_repo = MagicMock()
    service = _service(
        request_repo=request_repo,
        request_item_repo=request_item_repo,
        order_repo=order_repo,
    )

    payload = PurchaseRequestCreateSchema(
        tipo_compra=PurchaseType.INSUMO,
        itens=[PurchaseRequestItemCreateSchema(id_produto=1, quantidade=2.0)],
    )

    created_request = PurchaseRequestModel(
        id_solicitacao=10,
        data_solicitacao=date.today(),
        status=PurchaseRequestStatus.RASCUNHO,
        tipo_compra=PurchaseType.INSUMO,
        observacao=None,
        id_tipo_maquina=None,
        patrimonio=None,
        id_fazenda=None,
    )

    with patch("app.compras.service.get_session") as mock_session:
        session = MagicMock()
        mock_session.return_value.__enter__.return_value = session

        def flush_side_effect():
            if session.add.call_count == 1:
                added = session.add.call_args[0][0]
                if isinstance(added, PurchaseRequestModel):
                    added.id_solicitacao = 10

        session.flush.side_effect = flush_side_effect
        request_repo.get_by_id.return_value = created_request
        order_repo.get_by_solicitacao.return_value = None
        request_item_repo.list_with_product_labels.return_value = []

        service.create_request(payload)

    order_repo.create.assert_not_called()


def test_request_status_transition_rascunho_to_enviada_to_aprovada():
    request = PurchaseRequestModel(
        id_solicitacao=1,
        data_solicitacao=date.today(),
        status=PurchaseRequestStatus.RASCUNHO,
        tipo_compra=PurchaseType.INSUMO,
        observacao=None,
        id_tipo_maquina=None,
        patrimonio=None,
        id_fazenda=None,
    )
    request_repo = MagicMock()
    request_repo.get_by_id.return_value = request
    request_repo.update.side_effect = lambda _id, data: PurchaseRequestModel(
        **{**request.__dict__, **data}
    )
    order_repo = MagicMock()
    order_repo.get_by_solicitacao.return_value = None
    service = _service(request_repo=request_repo, order_repo=order_repo)

    from app.compras.schemas.purchase_request import PurchaseRequestUpdateSchema

    service.update_request(1, PurchaseRequestUpdateSchema(status=PurchaseRequestStatus.ENVIADA))
    request.status = PurchaseRequestStatus.ENVIADA
    service.update_request(1, PurchaseRequestUpdateSchema(status=PurchaseRequestStatus.APROVADA))
    assert request_repo.update.call_count == 2


def test_select_winning_quotation_creates_order_with_prices():
    request = PurchaseRequestModel(
        id_solicitacao=5,
        data_solicitacao=date.today(),
        status=PurchaseRequestStatus.APROVADA,
        tipo_compra=PurchaseType.INSUMO,
        observacao=None,
        id_tipo_maquina=None,
        patrimonio=None,
        id_fazenda=None,
    )
    quotation = SupplierQuotationModel(
        id_cotacao=7,
        id_solicitacao=5,
        id_fornecedor=3,
        status=QuotationStatus.ENVIADA,
        prazo_entrega_dias=5,
        observacao=None,
    )
    req_item = PurchaseRequestItemModel(
        id_item=11, id_solicitacao=5, id_produto=100, quantidade=4.0
    )
    q_item = QuotationItemModel(
        id_item_cotacao=1,
        id_cotacao=7,
        id_produto=100,
        quantidade=4.0,
        preco_unitario=12.5,
    )
    order = OrderModel(
        id_pedido=99,
        id_fornecedor=3,
        data_pedido=date.today(),
        status=OrderStatus.ABERTO,
        id_solicitacao=5,
        tipo_compra=PurchaseType.INSUMO,
    )

    request_repo = MagicMock()
    request_repo.get_by_id.return_value = request
    quotation_repo = MagicMock()
    quotation_repo.get_by_id.return_value = quotation
    quotation_repo.list.return_value = [quotation]
    quotation_item_repo = MagicMock()
    quotation_item_repo.list.return_value = [q_item]
    request_item_repo = MagicMock()
    request_item_repo.list.return_value = [req_item]
    order_repo = MagicMock()
    order_repo.get_by_solicitacao.side_effect = [None, None]
    order_repo.get_with_supplier_name.return_value = (order, "Fornecedor X")

    service = _service(
        request_repo=request_repo,
        quotation_repo=quotation_repo,
        quotation_item_repo=quotation_item_repo,
        request_item_repo=request_item_repo,
        order_repo=order_repo,
    )

    with patch.object(service, "convert_request_to_order", return_value=service._to_order_read(order, "Fornecedor X")) as convert_mock:
        result = service.select_winning_quotation(7)
        convert_mock.assert_called_once()
        args = convert_mock.call_args[0]
        assert args[0] == 5
        payload = args[1]
        assert payload.id_fornecedor == 3
        assert payload.item_prices[11] == 12.5
        assert result.id_pedido == 99


def test_create_invoice_linked_to_order():
    order = OrderModel(
        id_pedido=1,
        id_fornecedor=2,
        data_pedido=date.today(),
        status=OrderStatus.ABERTO,
        tipo_compra=PurchaseType.INSUMO,
        id_solicitacao=None,
    )
    order_repo = MagicMock()
    order_repo.get_by_id.return_value = order
    invoice_repo = MagicMock()
    invoice_repo.create.return_value = MagicMock(
        id_nota_fiscal=1,
        id_pedido=1,
        id_fornecedor=2,
        numero="123",
        serie="1",
        data_emissao=date.today(),
        valor_total=100.0,
        chave_acesso=None,
    )
    service = _service(order_repo=order_repo, invoice_repo=invoice_repo)

    invoice = service.create_invoice(
        1,
        PurchaseInvoiceCreateSchema(
            numero="123",
            serie="1",
            data_emissao=date.today(),
            valor_total=100.0,
        ),
    )
    assert invoice is not None
    assert invoice.id_pedido == 1
    invoice_repo.create.assert_called_once()


def test_equipment_order_approval_registers_machine():
    order = OrderModel(
        id_pedido=8,
        id_fornecedor=1,
        data_pedido=date.today(),
        status=OrderStatus.APROVADO,
        tipo_compra=PurchaseType.EQUIPAMENTO,
        id_solicitacao=3,
    )
    detail = EquipmentPurchaseDetailModel(
        id_pedido=8,
        id_tipo_maquina=2,
        patrimonio="PAT-001",
        id_fazenda=1,
        id_maquina=None,
    )
    order_repo = MagicMock()
    order_repo.get_by_id.return_value = order
    equipment_repo = MagicMock()
    equipment_repo.get_by_id.return_value = detail
    manutencao = MagicMock()
    manutencao.create_maquina.return_value = MagicMock(id_maquina=55)

    service = _service(
        order_repo=order_repo,
        equipment_detail_repo=equipment_repo,
        manutencao_service=manutencao,
    )
    service.register_equipment_from_order(8)
    manutencao.create_maquina.assert_called_once()
    equipment_repo.update.assert_called_once_with(8, {"id_maquina": 55})
