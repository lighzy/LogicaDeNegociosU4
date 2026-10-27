"""Captura salidas reales y operaciones Swagger. Uso: python scripts/capturar_evidencias.py."""
import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright, expect

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "evidencias"
URL = "http://127.0.0.1:8000"


def command(args, filename):
    result = subprocess.run([sys.executable, *args], cwd=BASE, capture_output=True, text=True)
    output = result.stdout + result.stderr
    (OUT / filename).write_text(output, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(output)
    return output


def main():
    OUT.mkdir(exist_ok=True)
    outputs = [
        ("Carga de los 16 pedidos originales", "python cargar_csv.py", command(["cargar_csv.py"], "carga.txt"), "01_carga.png"),
        ("Validación automática con pytest", "python -m pytest -q", command(["-m", "pytest", "-q"], "pytest.txt"), "02_pytest.png"),
    ]
    command(["-m", "pytest", "-v"], "pytest_detallado.txt")
    command(["scripts/ejecutar_escenarios.py"], "escenarios.txt")
    server = None
    try:
        try:
            httpx.get(URL + "/openapi.json", timeout=2, trust_env=False).raise_for_status()
        except httpx.HTTPError:
            server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.api:app", "--port", "8000"],
                                      cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(50):
                try:
                    if httpx.get(URL + "/openapi.json", timeout=1, trust_env=False).status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(.1)
            else:
                raise RuntimeError("No inició el servidor")
        assert httpx.get(URL + "/orders/O013", trust_env=False).json()["status"] == "DRAFT", "Reinicia el servidor: O013 debe iniciar DRAFT"
        (OUT / "openapi.json").write_text(json.dumps(httpx.get(URL + "/openapi.json", trust_env=False).json(), indent=2, ensure_ascii=False), encoding="utf-8")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=1)
            for title, cmd, output, filename in outputs:
                page.set_content(f'''<!doctype html><meta charset="utf-8"><style>
                    body{{margin:0;padding:40px;background:#edf2f7;color:#172033;font-family:Arial}}
                    h1{{font-size:27px;margin:0 0 12px}}p{{font-size:16px;color:#475569}}
                    pre{{background:#111827;color:#e2e8f0;border-radius:12px;padding:25px;
                    font:18px/1.55 monospace;white-space:pre-wrap;overflow-wrap:anywhere}}
                    </style><h1>{html.escape(title)}</h1><p>TechStore U4 · Salida real de ejecución · {html.escape(cmd)}</p>
                    <pre>{html.escape(output)}</pre><p>Fuente íntegra: evidencias/{'carga.txt' if 'carga' in filename else 'pytest.txt'}</p>''')
                page.screenshot(path=str(OUT / filename), full_page=True)
            page.goto(URL + "/docs")
            block = page.locator('.opblock-post').filter(has_text='/orders/{order_id}/confirm')
            block.locator('.opblock-summary').click()
            block.get_by_role('button', name='Try it out').click()
            block.locator('input[type="text"]').fill('O013')
            records = []
            for expected_status, filename in [(200, '03_swagger_200.png'), (409, '04_swagger_409.png')]:
                with page.expect_response(lambda r: r.url.endswith('/orders/O013/confirm') and r.request.method == 'POST') as info:
                    block.get_by_role('button', name='Execute', exact=True).click()
                response = info.value
                assert response.status == expected_status
                records.append({"url": response.url, "status": response.status, "body": response.json()})
                expect(block.locator('.responses-inner .response-col_status:not(.col_header)').first).to_contain_text(str(expected_status))
                block.screenshot(path=str(OUT / filename))
            (OUT / 'swagger_respuestas.json').write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding='utf-8')
            browser.close()
        print("Capturas y logs generados correctamente")
    finally:
        if server:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    main()
