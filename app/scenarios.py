"""Ejecución reproducible de los escenarios originales, uno por fixture nuevo."""
from decimal import Decimal
from app.domain import DomainException, OrderItem, Money
from app.specifications import calculate_discount
from cargar_csv import load_fixture, rows


def execute_scenario(case):
    orders = load_fixture()
    order = orders[case["pedido_id"]]
    initial = {"status": order.status.value, "units": order.units,
               "total": str(order.total.amount), "customer": order.customer.id,
               "vip": order.customer.is_vip, "active": order.customer.active,
               "promotion": order.has_promotion}
    steps = []

    def run(operation, action):
        before = (order.status, order.items, order.events, order.tracking_number,
                  order.cancellation_reason)
        start = len(order.events)
        try:
            action()
            steps.append({"operation": operation, "result": "éxito",
                          "status": order.status.value,
                          "events": [e.name for e in order.events[start:]]})
        except DomainException as exc:
            after = (order.status, order.items, order.events, order.tracking_number,
                     order.cancellation_reason)
            assert after == before, "Una operación rechazada modificó el agregado"
            steps.append({"operation": operation, "result": type(exc).__name__,
                          "message": str(exc), "status": order.status.value, "events": []})

    cid = case["caso_id"]
    quote = calculate_discount(order)
    if case["accion"] == "evaluar_descuento":
        run("calculate_discount()", lambda: calculate_discount(order))
    elif cid in {"E03", "E06", "E07"}:
        run("confirm()", order.confirm)
    elif cid == "E08":
        price = next(r["precio_mxn"] for r in rows("productos.csv") if r["sku"] == "SKU003")
        run("add_item(SKU003, 2)", lambda: order.add_item(OrderItem("SKU003", 2, Money(Decimal(price)))))
    else:
        run("confirm()", order.confirm)
        if cid == "E11":
            run('ship("")', lambda: order.ship(""))
        elif cid == "E12":
            run("confirm() por segunda vez", order.confirm)
        else:
            run('ship("GUIA-U4-001")', lambda: order.ship("GUIA-U4-001"))
            if cid == "E13":
                run('cancel("Solicitud del cliente")', lambda: order.cancel("Solicitud del cliente"))
            elif cid == "E14":
                run("return_order()", order.return_order)
            elif cid == "E15":
                run("deliver()", order.deliver)
            else:
                raise ValueError(f"Escenario desconocido: {cid}")
    return {"case": cid, "order": order.id, "initial": initial, "steps": steps,
            "final_status": order.status.value, "final_units": order.units,
            "rate": str(quote.rate), "discount": str(quote.discount.amount),
            "payable": str(quote.payable.amount), "events": [e.name for e in order.events]}
