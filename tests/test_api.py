import pytest
from fastapi.testclient import TestClient
from app.api import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client


def test_lectura_y_descuento(client):
    assert len(client.get("/orders").json()) == 16
    data = client.get("/orders/O001").json()
    assert data["total"] == "2100.00" and data["payable"] == "1890.00"
    assert data["status"] == "DRAFT"


@pytest.mark.parametrize("path,method", [("/orders/NO-EXISTE", "get"), ("/orders/NO-EXISTE/confirm", "post")])
def test_404(client, path, method):
    assert getattr(client, method)(path).status_code == 404


def test_confirmacion_doble_409(client):
    assert client.post("/orders/O013/confirm").status_code == 200
    before = client.get("/orders/O013").json()
    assert client.post("/orders/O013/confirm").status_code == 409
    assert client.get("/orders/O013").json() == before


@pytest.mark.parametrize("oid", ["O003", "O004", "O007"])
def test_422_confirmacion(client, oid):
    assert client.post(f"/orders/{oid}/confirm").status_code == 422
    assert client.get(f"/orders/{oid}").json()["events"] == []


def test_envio_y_rechazos(client):
    client.post("/orders/O012/confirm")
    assert client.post("/orders/O012/ship", json={"tracking_number": ""}).status_code == 422
    assert client.post("/orders/O012/ship", json={"tracking_number": "G-123"}).status_code == 200
    assert client.post("/orders/O012/cancel", json={"reason": "M"}).status_code == 409


def test_cancelacion(client):
    client.post("/orders/O001/confirm")
    assert client.post("/orders/O001/cancel", json={"reason": " "}).status_code == 422
    result = client.post("/orders/O001/cancel", json={"reason": "Cambio de compra"})
    assert result.status_code == 200 and result.json()["status"] == "CANCELLED"


@pytest.mark.parametrize("action,state", [("return", "RETURNED"), ("deliver", "DELIVERED")])
def test_finalizacion(client, action, state):
    client.post("/orders/O015/confirm")
    client.post("/orders/O015/ship", json={"tracking_number": "G"})
    response = client.post(f"/orders/O015/{action}")
    assert response.status_code == 200 and response.json()["status"] == state


@pytest.mark.parametrize("body,status", [
    ({"sku": "SKU003", "quantity": 2}, 422),
    ({"sku": "SKU003", "quantity": 0}, 422),
    ({"sku": "SKU003", "quantity": 1.5}, 422),
    ({"sku": "SKU003", "quantity": True}, 422),
    ({"sku": "NO", "quantity": 1}, 404),
    ({"sku": "SKU003", "quantity": 1}, 200),
])
def test_agregar(client, body, status):
    assert client.post("/orders/O009/items", json=body).status_code == status


def test_openapi_y_swagger_local(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/swagger-assets/swagger-ui-bundle.js").status_code == 200
    assert "/orders/{order_id}/confirm" in client.get("/openapi.json").json()["paths"]
