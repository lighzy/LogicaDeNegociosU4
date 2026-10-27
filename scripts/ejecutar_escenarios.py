"""Genera la bitácora a partir de operaciones reales del dominio."""
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.scenarios import execute_scenario
from cargar_csv import rows

BASE = Path(__file__).resolve().parents[1]

def main():
    cases = rows("escenarios.csv")
    results = [execute_scenario(c) for c in cases]
    (BASE / "evidencias/escenarios.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = []
    text = ["# Bitácora resuelta de E01 a E15", "",
            "Cada escenario utiliza una carga nueva de los CSV originales. Todos empiezan DRAFT. "
            "Un rechazo conserva los pasos válidos anteriores. Los importes son MXN; el total bruto "
            "no se modifica al cotizar el descuento.", ""]
    for c, r in zip(cases, results):
        i = r["initial"]
        pre = f'{r["order"]}; DRAFT; cliente {i["customer"]}; VIP={i["vip"]}; activo={i["active"]}; promoción={i["promotion"]}; {i["units"]} unidades; total {i["total"]} MXN'
        outcome = "; ".join(f'{s["operation"]}: {s["result"]} → {s["status"]}' for s in r["steps"])
        if c["accion"] == "evaluar_descuento":
            outcome += f'; tasa {r["rate"]}; descuento {r["discount"]}; a pagar {r["payable"]} MXN'
        events = "; ".join(f'{s["operation"]}: {", ".join(s["events"]) or "ninguno"}' for s in r["steps"])
        test = f'tests/test_scenarios.py::test_escenario[{r["case"]}]'
        summary.append([r["case"], pre, c["accion"], outcome, events, c["pista"], test])
        text += [f'## {r["case"]} · {r["order"]}', "", f'**Precondiciones:** {pre}.', "",
                 f'**Operación:** {c["accion"]}.', "", f'**Resultado real:** {outcome}.', "",
                 f'**Eventos por paso:** {events}.', "", f'**Explicación:** {c["pista"]}.', "",
                 f'**Prueba:** `{test}`.', ""]
    text += ["## Observaciones", "",
             "O010 tiene total exacto de 500, pero tampoco es VIP y tiene solo 2 unidades. "
             "La prueba adicional test_umbral_500_aislado usa pedidos nuevos VIP de 4 unidades "
             "para comparar 500 frente a 500.04, sin alterar los CSV.", "",
             "O003 satisface la regla matemática del descuento VIP, pero no puede confirmarse: "
             "la actividad del cliente es precondición de confirmación, no condición del descuento.", "",
             "O004 se carga aunque no tenga escenario propio; también se cubre en las pruebas HTTP de cliente inactivo."]
    (BASE / "docs/BITACORA.md").write_text("\n".join(text), encoding="utf-8")
    with (BASE / "docs/BITACORA.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["caso", "precondiciones", "operacion", "resultado real", "evento", "explicacion", "prueba"])
        w.writerows(summary)
    for r in results:
        print(f'{r["case"]} {r["order"]} -> {r["final_status"]}: {r["steps"][-1]["result"]}')

if __name__ == "__main__":
    main()
