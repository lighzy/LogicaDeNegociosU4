from dataclasses import FrozenInstanceError
from decimal import Decimal
import pytest
from app.domain import (Money, Customer, OrderItem, Order, OrderStatus,
                        InvalidOrderData, InvalidOrderTransition)
from app.specifications import (calculate_discount, MinimumAmountSpec,
                                VIPCustomerSpec, ActivePromotionSpec)
from cargar_csv import load_fixture, rows


def test_carga_original():
    orders = load_fixture()
    assert len(orders) == 16
    assert len(rows("clientes.csv")) == len(rows("productos.csv")) == 12
    assert len(rows("detalle_pedidos.csv")) == 21
    assert all(o.status == OrderStatus.DRAFT and not o.events for o in orders.values())
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")
    assert load_fixture()["O001"] is not orders["O001"]


@pytest.mark.parametrize("amount", [Decimal("-1"), Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), 1.5, 10, "10"])
def test_money_invalido(amount):
    with pytest.raises(InvalidOrderData):
        Money(amount)


def test_money_suma_inmutable_y_moneda():
    a = Money(Decimal("0.1"))
    assert a.add(Money(Decimal("0.2"))).amount == Decimal("0.3")
    assert a.amount == Decimal("0.1")
    with pytest.raises(FrozenInstanceError):
        a.amount = Decimal("3")
    with pytest.raises(InvalidOrderData):
        a.add(Money(Decimal("1"), "USD"))


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True])
def test_cantidad_invalida(quantity):
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU", quantity, Money(Decimal("1")))


def test_sku_vacio_y_moneda_en_pedido():
    with pytest.raises(InvalidOrderData):
        OrderItem("  ", 1, Money(Decimal("1")))
    o = Order(Customer("C"), "O")
    with pytest.raises(InvalidOrderData):
        o.add_item(OrderItem("X", 1, Money(Decimal("1"), "USD")))
    assert o.units == 0


def test_limite_es_suma_no_lineas():
    o = load_fixture()["O009"]
    o.add_item(OrderItem("SKU003", 1, Money(Decimal("120"))))
    assert len(o.items) == 2 and o.units == 20
    before = o.items
    with pytest.raises(InvalidOrderData):
        o.add_item(OrderItem("SKU003", 1, Money(Decimal("120"))))
    assert o.items == before


@pytest.mark.parametrize("total,expected", [("500", "0"), ("500.04", "0.10")])
def test_umbral_500_aislado(total, expected):
    # O010 no aísla el umbral: además NO es VIP y tiene solo 2 unidades.
    o = Order(Customer("C", True), "O")
    o.add_item(OrderItem("X", 4, Money(Decimal(total) / 4)))
    assert calculate_discount(o).rate == Decimal(expected)


@pytest.mark.parametrize("total,expected", [("5000", "0"), ("5000.01", "0.05")])
def test_umbral_5000_aislado(total, expected):
    o = Order(Customer("C"), "O")
    o.add_item(OrderItem("X", 1, Money(Decimal(total))))
    assert calculate_discount(o).rate == Decimal(expected)


@pytest.mark.parametrize("promo,expected", [(False, "0.10"), (True, "0")])
def test_prioridad_y_promocion_bloquea_ambas(promo, expected):
    o = Order(Customer("C", True), "O", promo)
    o.add_item(OrderItem("X", 4, Money(Decimal("2000"))))
    assert calculate_discount(o).rate == Decimal(expected)


def test_composicion_or_and_not_sin_efectos():
    o = load_fixture()["O006"]
    before = (o.items, o.status, o.events)
    a, b = VIPCustomerSpec(), MinimumAmountSpec(Decimal("5000"))
    assert (a | b).is_satisfied_by(o)
    assert not (a & b).is_satisfied_by(o)
    assert (~ActivePromotionSpec()).is_satisfied_by(o)
    assert (o.items, o.status, o.events) == before


def test_cancelacion_valida_y_evento():
    o = load_fixture()["O001"]
    o.confirm()
    o.cancel(" Solicitud del cliente ")
    assert o.status == OrderStatus.CANCELLED
    assert o.cancellation_reason == "Solicitud del cliente"
    assert [e.name for e in o.events] == ["OrderConfirmed", "OrderCancelled"]
    assert all(e.order_id == o.id and e.occurred_at.utcoffset().total_seconds() == 0 for e in o.events)


@pytest.mark.parametrize("method", ["ship", "cancel"])
def test_texto_vacio_no_muta(method):
    o = load_fixture()["O001"]
    o.confirm()
    events = o.events
    with pytest.raises(InvalidOrderData):
        getattr(o, method)("   ")
    assert o.status == OrderStatus.CONFIRMED and o.events == events
    assert o.tracking_number is None and o.cancellation_reason is None


@pytest.mark.parametrize("state", list(OrderStatus))
@pytest.mark.parametrize("method,required,args", [
    ("confirm", OrderStatus.DRAFT, ()),
    ("ship", OrderStatus.CONFIRMED, ("GUIA",)),
    ("cancel", OrderStatus.CONFIRMED, ("Motivo",)),
    ("deliver", OrderStatus.SHIPPED, ()),
    ("return_order", OrderStatus.SHIPPED, ()),
])
def test_matriz_transiciones(state, method, required, args):
    o = load_fixture()["O001"]
    if state != OrderStatus.DRAFT:
        o.confirm()
    if state in {OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.RETURNED}:
        o.ship("G")
    if state == OrderStatus.CANCELLED:
        o.cancel("M")
    if state == OrderStatus.DELIVERED:
        o.deliver()
    if state == OrderStatus.RETURNED:
        o.return_order()
    before = (o.status, o.events)
    if state == required:
        getattr(o, method)(*args)
        assert len(o.events) == len(before[1]) + 1
    else:
        with pytest.raises(InvalidOrderTransition):
            getattr(o, method)(*args)
        assert (o.status, o.events) == before


def test_agregar_despues_de_confirmar():
    o = load_fixture()["O001"]
    o.confirm()
    before = (o.items, o.events)
    with pytest.raises(InvalidOrderTransition):
        o.add_item(OrderItem("X", 1, Money(Decimal("1"))))
    assert (o.items, o.events) == before
