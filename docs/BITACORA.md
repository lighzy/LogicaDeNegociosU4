# Bitácora resuelta de E01 a E15

Cada escenario utiliza una carga nueva de los CSV originales. Todos empiezan DRAFT. Un rechazo conserva los pasos válidos anteriores. Los importes son MXN; el total bruto no se modifica al cotizar el descuento.

## E01 · O001

**Precondiciones:** O001; DRAFT; cliente C001; VIP=True; activo=True; promoción=False; 4 unidades; total 2100.00 MXN.

**Operación:** evaluar_descuento.

**Resultado real:** calculate_discount(): éxito → DRAFT; tasa 0.10; descuento 210.00; a pagar 1890.00 MXN.

**Eventos por paso:** calculate_discount(): ninguno.

**Explicación:** AND VIP + monto >500 + unidades >=4 + NOT promo.

**Prueba:** `tests/test_scenarios.py::test_escenario[E01]`.

## E02 · O002

**Precondiciones:** O002; DRAFT; cliente C002; VIP=False; activo=True; promoción=False; 2 unidades; total 1050.00 MXN.

**Operación:** evaluar_descuento.

**Resultado real:** calculate_discount(): éxito → DRAFT; tasa 0; descuento 0.00; a pagar 1050.00 MXN.

**Eventos por paso:** calculate_discount(): ninguno.

**Explicación:** No VIP, total menor a 5000.

**Prueba:** `tests/test_scenarios.py::test_escenario[E02]`.

## E03 · O003

**Precondiciones:** O003; DRAFT; cliente C003; VIP=True; activo=False; promoción=False; 4 unidades; total 2100.00 MXN.

**Operación:** confirmar.

**Resultado real:** confirm(): InvalidOrderData → DRAFT.

**Eventos por paso:** confirm(): ninguno.

**Explicación:** Cliente inactivo.

**Prueba:** `tests/test_scenarios.py::test_escenario[E03]`.

## E04 · O005

**Precondiciones:** O005; DRAFT; cliente C005; VIP=True; activo=True; promoción=True; 4 unidades; total 2100.00 MXN.

**Operación:** evaluar_descuento.

**Resultado real:** calculate_discount(): éxito → DRAFT; tasa 0; descuento 0.00; a pagar 2100.00 MXN.

**Eventos por paso:** calculate_discount(): ninguno.

**Explicación:** Promocion activa bloquea descuento.

**Prueba:** `tests/test_scenarios.py::test_escenario[E04]`.

## E05 · O006

**Precondiciones:** O006; DRAFT; cliente C006; VIP=False; activo=True; promoción=False; 1 unidades; total 18000.00 MXN.

**Operación:** evaluar_descuento.

**Resultado real:** calculate_discount(): éxito → DRAFT; tasa 0.05; descuento 900.00; a pagar 17100.00 MXN.

**Eventos por paso:** calculate_discount(): ninguno.

**Explicación:** OR total >5000 y sin promocion.

**Prueba:** `tests/test_scenarios.py::test_escenario[E05]`.

## E06 · O007

**Precondiciones:** O007; DRAFT; cliente C007; VIP=True; activo=True; promoción=False; 0 unidades; total 0 MXN.

**Operación:** confirmar.

**Resultado real:** confirm(): InvalidOrderData → DRAFT.

**Eventos por paso:** confirm(): ninguno.

**Explicación:** Pedido sin articulos.

**Prueba:** `tests/test_scenarios.py::test_escenario[E06]`.

## E07 · O008

**Precondiciones:** O008; DRAFT; cliente C008; VIP=False; activo=True; promoción=False; 20 unidades; total 2400.00 MXN.

**Operación:** confirmar.

**Resultado real:** confirm(): éxito → CONFIRMED.

**Eventos por paso:** confirm(): OrderConfirmed.

**Explicación:** 20 unidades permitidas.

**Prueba:** `tests/test_scenarios.py::test_escenario[E07]`.

## E08 · O009

**Precondiciones:** O009; DRAFT; cliente C009; VIP=True; activo=True; promoción=False; 19 unidades; total 2280.00 MXN.

**Operación:** agregar SKU003 x2.

**Resultado real:** add_item(SKU003, 2): OrderItemLimitExceeded → DRAFT.

**Eventos por paso:** add_item(SKU003, 2): ninguno.

**Explicación:** 21 unidades excede limite.

**Prueba:** `tests/test_scenarios.py::test_escenario[E08]`.

## E09 · O010

**Precondiciones:** O010; DRAFT; cliente C010; VIP=False; activo=True; promoción=False; 2 unidades; total 500.00 MXN.

**Operación:** evaluar_descuento.

**Resultado real:** calculate_discount(): éxito → DRAFT; tasa 0; descuento 0.00; a pagar 500.00 MXN.

**Eventos por paso:** calculate_discount(): ninguno.

**Explicación:** Umbral estricto >500.

**Prueba:** `tests/test_scenarios.py::test_escenario[E09]`.

## E10 · O011

**Precondiciones:** O011; DRAFT; cliente C011; VIP=True; activo=True; promoción=False; 3 unidades; total 1500.00 MXN.

**Operación:** evaluar_descuento.

**Resultado real:** calculate_discount(): éxito → DRAFT; tasa 0; descuento 0.00; a pagar 1500.00 MXN.

**Eventos por paso:** calculate_discount(): ninguno.

**Explicación:** Solo 3 unidades, requiere 4.

**Prueba:** `tests/test_scenarios.py::test_escenario[E10]`.

## E11 · O012

**Precondiciones:** O012; DRAFT; cliente C012; VIP=False; activo=True; promoción=False; 1 unidades; total 850.00 MXN.

**Operación:** confirmar y enviar sin guia.

**Resultado real:** confirm(): éxito → CONFIRMED; ship(""): InvalidOrderData → CONFIRMED.

**Eventos por paso:** confirm(): OrderConfirmed; ship(""): ninguno.

**Explicación:** La confirmacion es valida pero falta guia.

**Prueba:** `tests/test_scenarios.py::test_escenario[E11]`.

## E12 · O013

**Precondiciones:** O013; DRAFT; cliente C001; VIP=True; activo=True; promoción=False; 1 unidades; total 600.00 MXN.

**Operación:** confirmar dos veces.

**Resultado real:** confirm(): éxito → CONFIRMED; confirm() por segunda vez: InvalidOrderTransition → CONFIRMED.

**Eventos por paso:** confirm(): OrderConfirmed; confirm() por segunda vez: ninguno.

**Explicación:** No permite confirmar desde CONFIRMED.

**Prueba:** `tests/test_scenarios.py::test_escenario[E12]`.

## E13 · O014

**Precondiciones:** O014; DRAFT; cliente C002; VIP=False; activo=True; promoción=False; 1 unidades; total 600.00 MXN.

**Operación:** confirmar, enviar y cancelar.

**Resultado real:** confirm(): éxito → CONFIRMED; ship("GUIA-U4-001"): éxito → SHIPPED; cancel("Solicitud del cliente"): InvalidOrderTransition → SHIPPED.

**Eventos por paso:** confirm(): OrderConfirmed; ship("GUIA-U4-001"): OrderShipped; cancel("Solicitud del cliente"): ninguno.

**Explicación:** No permite cancelar desde SHIPPED.

**Prueba:** `tests/test_scenarios.py::test_escenario[E13]`.

## E14 · O015

**Precondiciones:** O015; DRAFT; cliente C005; VIP=True; activo=True; promoción=False; 1 unidades; total 450.00 MXN.

**Operación:** confirmar, enviar y devolver.

**Resultado real:** confirm(): éxito → CONFIRMED; ship("GUIA-U4-001"): éxito → SHIPPED; return_order(): éxito → RETURNED.

**Eventos por paso:** confirm(): OrderConfirmed; ship("GUIA-U4-001"): OrderShipped; return_order(): OrderReturned.

**Explicación:** Termina en RETURNED.

**Prueba:** `tests/test_scenarios.py::test_escenario[E14]`.

## E15 · O016

**Precondiciones:** O016; DRAFT; cliente C007; VIP=True; activo=True; promoción=False; 1 unidades; total 2100.00 MXN.

**Operación:** confirmar, enviar y entregar.

**Resultado real:** confirm(): éxito → CONFIRMED; ship("GUIA-U4-001"): éxito → SHIPPED; deliver(): éxito → DELIVERED.

**Eventos por paso:** confirm(): OrderConfirmed; ship("GUIA-U4-001"): OrderShipped; deliver(): OrderDelivered.

**Explicación:** Termina en DELIVERED.

**Prueba:** `tests/test_scenarios.py::test_escenario[E15]`.

## Observaciones

O010 tiene total exacto de 500, pero tampoco es VIP y tiene solo 2 unidades. La prueba adicional test_umbral_500_aislado usa pedidos nuevos VIP de 4 unidades para comparar 500 frente a 500.04, sin alterar los CSV.

O003 satisface la regla matemática del descuento VIP, pero no puede confirmarse: la actividad del cliente es precondición de confirmación, no condición del descuento.

O004 se carga aunque no tenga escenario propio; también se cubre en las pruebas HTTP de cliente inactivo.