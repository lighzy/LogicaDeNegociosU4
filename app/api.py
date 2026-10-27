"""API REST. El dominio decide reglas; la interfaz traduce excepciones a HTTP."""
from dataclasses import asdict
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, StrictInt
from pathlib import Path
from app.domain import InvalidOrderData, InvalidOrderTransition, Money, OrderItem
from app.specifications import calculate_discount
from cargar_csv import load_fixture, rows


class ShipmentBody(BaseModel):
    tracking_number: str


class CancellationBody(BaseModel):
    reason: str


class ItemBody(BaseModel):
    sku: str
    quantity: StrictInt


def serialize(order):
    quote = calculate_discount(order)
    return {
        "id": order.id, "customer_id": order.customer.id,
        "status": order.status.value, "units": order.units,
        "currency": "MXN", "total": str(order.total.amount),
        "discount_rate": str(quote.rate), "discount": str(quote.discount.amount),
        "payable": str(quote.payable.amount),
        "tracking_number": order.tracking_number,
        "cancellation_reason": order.cancellation_reason,
        "events": jsonable_encoder([asdict(e) for e in order.events]),
    }


def create_app():
    app = FastAPI(title="TechStore U4", version="1.0.0", docs_url=None,
                  description="Pedidos en memoria · Actividad 4 · FIME UANL")
    app.state.orders = load_fixture()
    app.state.prices = {r["sku"]: Decimal(r["precio_mxn"]) for r in rows("productos.csv")}
    # Swagger se sirve localmente para que /docs funcione sin un CDN.
    app.mount("/swagger-assets", StaticFiles(directory=Path(__file__).parent / "static" / "swagger"), name="swagger")

    @app.get("/docs", include_in_schema=False)
    def docs():
        return get_swagger_ui_html(openapi_url=app.openapi_url, title="TechStore U4 — Swagger UI",
                                  swagger_js_url="/swagger-assets/swagger-ui-bundle.js",
                                  swagger_css_url="/swagger-assets/swagger-ui.css")

    @app.exception_handler(InvalidOrderData)
    async def invalid_data(request: Request, exc: InvalidOrderData):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InvalidOrderTransition)
    async def invalid_transition(request: Request, exc: InvalidOrderTransition):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    def find(order_id):
        order = app.state.orders.get(order_id)
        if order is None:
            raise HTTPException(404, "No existe")
        return order

    @app.get("/orders", tags=["Pedidos"])
    def list_orders():
        return [serialize(o) for o in app.state.orders.values()]

    @app.get("/orders/{order_id}", tags=["Pedidos"])
    def get_order(order_id: str):
        return serialize(find(order_id))

    @app.post("/orders/{order_id}/confirm", tags=["Transiciones"],
              responses={404: {"description": "Pedido inexistente"},
                         409: {"description": "Transición prohibida"},
                         422: {"description": "Pedido vacío o cliente inactivo"}})
    def confirm(order_id: str):
        order = find(order_id)
        order.confirm()
        return serialize(order)

    @app.post("/orders/{order_id}/ship", tags=["Transiciones"])
    def ship(order_id: str, body: ShipmentBody):
        order = find(order_id)
        order.ship(body.tracking_number)
        return serialize(order)

    @app.post("/orders/{order_id}/cancel", tags=["Transiciones"])
    def cancel(order_id: str, body: CancellationBody):
        order = find(order_id)
        order.cancel(body.reason)
        return serialize(order)

    @app.post("/orders/{order_id}/deliver", tags=["Transiciones"])
    def deliver(order_id: str):
        order = find(order_id)
        order.deliver()
        return serialize(order)

    @app.post("/orders/{order_id}/return", tags=["Transiciones"])
    def return_order(order_id: str):
        order = find(order_id)
        order.return_order()
        return serialize(order)

    @app.post("/orders/{order_id}/items", tags=["Pedidos"])
    def add_item(order_id: str, body: ItemBody):
        order = find(order_id)
        price = app.state.prices.get(body.sku)
        if price is None:
            raise HTTPException(404, "SKU inexistente")
        order.add_item(OrderItem(body.sku, body.quantity, Money(price)))
        return serialize(order)

    return app


app = create_app()
