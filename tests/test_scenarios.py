"""Oráculos explícitos: no se calculan a partir de la implementación."""
import pytest
from decimal import Decimal
from cargar_csv import rows
from app.scenarios import execute_scenario

EXPECTED = {
    "E01": ("DRAFT", 4, "0.10", "210.00", "1890.00", "éxito", []),
    "E02": ("DRAFT", 2, "0", "0.00", "1050.00", "éxito", []),
    "E03": ("DRAFT", 4, "0.10", "210.00", "1890.00", "InvalidOrderData", []),
    "E04": ("DRAFT", 4, "0", "0.00", "2100.00", "éxito", []),
    "E05": ("DRAFT", 1, "0.05", "900.00", "17100.00", "éxito", []),
    "E06": ("DRAFT", 0, "0", "0.00", "0.00", "InvalidOrderData", []),
    "E07": ("CONFIRMED", 20, "0", "0.00", "2400.00", "éxito", ["OrderConfirmed"]),
    "E08": ("DRAFT", 19, "0.10", "228.00", "2052.00", "OrderItemLimitExceeded", []),
    "E09": ("DRAFT", 2, "0", "0.00", "500.00", "éxito", []),
    "E10": ("DRAFT", 3, "0", "0.00", "1500.00", "éxito", []),
    "E11": ("CONFIRMED", 1, "0", "0.00", "850.00", "InvalidOrderData", ["OrderConfirmed"]),
    "E12": ("CONFIRMED", 1, "0", "0.00", "600.00", "InvalidOrderTransition", ["OrderConfirmed"]),
    "E13": ("SHIPPED", 1, "0", "0.00", "600.00", "InvalidOrderTransition", ["OrderConfirmed", "OrderShipped"]),
    "E14": ("RETURNED", 1, "0", "0.00", "450.00", "éxito", ["OrderConfirmed", "OrderShipped", "OrderReturned"]),
    "E15": ("DELIVERED", 1, "0", "0.00", "2100.00", "éxito", ["OrderConfirmed", "OrderShipped", "OrderDelivered"]),
}


@pytest.mark.parametrize("case", rows("escenarios.csv"), ids=lambda c: c["caso_id"])
def test_escenario(case):
    result = execute_scenario(case)
    status, units, rate, discount, payable, last_result, events = EXPECTED[case["caso_id"]]
    assert result["final_status"] == status
    assert result["final_units"] == units
    assert Decimal(result["rate"]) == Decimal(rate)
    assert Decimal(result["discount"]) == Decimal(discount)
    assert Decimal(result["payable"]) == Decimal(payable)
    assert result["steps"][-1]["result"] == last_result
    assert result["events"] == events
    if last_result != "éxito":
        assert result["steps"][-1]["events"] == []
