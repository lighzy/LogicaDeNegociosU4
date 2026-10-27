"""Dominio independiente de FastAPI y de los archivos CSV."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class DomainException(Exception):
    """Error controlado de negocio."""


class InvalidOrderData(DomainException):
    pass


class InvalidOrderTransition(DomainException):
    pass


class OrderItemLimitExceeded(InvalidOrderData):
    pass


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "MXN"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            raise InvalidOrderData("El importe debe ser Decimal, no float")
        if not self.amount.is_finite() or self.amount < 0:
            raise InvalidOrderData("Monto inválido")
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise InvalidOrderData("Moneda inválida")

    def add(self, other):
        if self.currency != other.currency:
            raise InvalidOrderData("Monedas distintas")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class Customer:
    id: str
    is_vip: bool = False
    active: bool = True


@dataclass(frozen=True)
class OrderItem:
    sku: str
    quantity: int
    unit_price: Money

    def __post_init__(self):
        if (not isinstance(self.sku, str) or not self.sku.strip()
                or type(self.quantity) is not int or self.quantity <= 0):
            raise InvalidOrderData("Artículo inválido")
        if not isinstance(self.unit_price, Money):
            raise InvalidOrderData("Se requiere un precio Money")

    @property
    def subtotal(self):
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


@dataclass(frozen=True)
class DomainEvent:
    name: str
    order_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Order:
    """Aggregate Root: colecciones de solo lectura; cambios mediante métodos."""

    def __init__(self, customer: Customer, id: str, has_promotion: bool = False):
        self.customer = customer
        self.id = id
        self.has_promotion = has_promotion
        self._status = OrderStatus.DRAFT
        self._items = []
        self._events = []
        self.tracking_number = None
        self.cancellation_reason = None

    @property
    def status(self):
        return self._status

    @property
    def items(self):
        return tuple(self._items)

    @property
    def events(self):
        return tuple(self._events)

    @property
    def units(self):
        return sum(item.quantity for item in self._items)

    @property
    def total(self):
        return Money(sum((item.subtotal.amount for item in self._items), Decimal("0")))

    def _require(self, status):
        if self.status != status:
            raise InvalidOrderTransition(f"Requiere {status.value}; estado actual {self.status.value}")

    def _transition(self, status, event):
        self._status = status
        self._events.append(DomainEvent(event, self.id))

    def add_item(self, item):
        self._require(OrderStatus.DRAFT)
        if self.units + item.quantity > 20:
            raise OrderItemLimitExceeded("Máximo 20 unidades")
        if item.unit_price.currency != "MXN":
            raise InvalidOrderData("Solo MXN")
        self._items.append(item)

    def confirm(self):
        self._require(OrderStatus.DRAFT)
        if not self.items or not self.customer.active:
            raise InvalidOrderData("Requiere artículos y cliente activo")
        self._transition(OrderStatus.CONFIRMED, "OrderConfirmed")

    def ship(self, tracking_number):
        self._require(OrderStatus.CONFIRMED)
        if not isinstance(tracking_number, str) or not tracking_number.strip():
            raise InvalidOrderData("Guía obligatoria")
        self.tracking_number = tracking_number.strip()
        self._transition(OrderStatus.SHIPPED, "OrderShipped")

    def cancel(self, reason):
        self._require(OrderStatus.CONFIRMED)
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidOrderData("Motivo obligatorio")
        self.cancellation_reason = reason.strip()
        self._transition(OrderStatus.CANCELLED, "OrderCancelled")

    def deliver(self):
        self._require(OrderStatus.SHIPPED)
        self._transition(OrderStatus.DELIVERED, "OrderDelivered")

    def return_order(self):
        self._require(OrderStatus.SHIPPED)
        self._transition(OrderStatus.RETURNED, "OrderReturned")
