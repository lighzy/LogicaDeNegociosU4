"""Reglas puras y componibles: no mutan pedidos ni emiten eventos."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from app.domain import Money


class Specification:
    def is_satisfied_by(self, order):
        raise NotImplementedError

    def __and__(self, other):
        return AndSpec(self, other)

    def __or__(self, other):
        return OrSpec(self, other)

    def __invert__(self):
        return NotSpec(self)


@dataclass(frozen=True)
class AndSpec(Specification):
    left: Specification
    right: Specification

    def is_satisfied_by(self, order):
        return self.left.is_satisfied_by(order) and self.right.is_satisfied_by(order)


@dataclass(frozen=True)
class OrSpec(Specification):
    left: Specification
    right: Specification

    def is_satisfied_by(self, order):
        return self.left.is_satisfied_by(order) or self.right.is_satisfied_by(order)


@dataclass(frozen=True)
class NotSpec(Specification):
    inner: Specification

    def is_satisfied_by(self, order):
        return not self.inner.is_satisfied_by(order)


@dataclass(frozen=True)
class MinimumAmountSpec(Specification):
    minimum: Decimal

    def is_satisfied_by(self, order):
        return order.total.amount > self.minimum


class VIPCustomerSpec(Specification):
    def is_satisfied_by(self, order):
        return order.customer.is_vip


@dataclass(frozen=True)
class MinimumUnitsSpec(Specification):
    minimum: int = 4

    def is_satisfied_by(self, order):
        return order.units >= self.minimum


class ActivePromotionSpec(Specification):
    def is_satisfied_by(self, order):
        return order.has_promotion


ten_percent = (MinimumAmountSpec(Decimal("500")) & VIPCustomerSpec()
               & MinimumUnitsSpec(4) & ~ActivePromotionSpec())
five_percent = MinimumAmountSpec(Decimal("5000")) & ~ActivePromotionSpec()
eligible_for_discount = ten_percent | five_percent


@dataclass(frozen=True)
class DiscountResult:
    rate: Decimal
    discount: Money
    payable: Money


def calculate_discount(order):
    rate = Decimal("0")
    if eligible_for_discount.is_satisfied_by(order):
        rate = Decimal("0.10") if ten_percent.is_satisfied_by(order) else Decimal("0.05")
    # Redondeo monetario explícito al final, no durante los subtotales.
    amount = (order.total.amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return DiscountResult(rate, Money(amount), Money(order.total.amount - amount))
