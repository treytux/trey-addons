Industry Stock Warehouse Orderpoint
===================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Extiende las órdenes de abastecimiento para calcular automáticamente la cantidad mínima en función del consumo histórico y generar sugerencias de compra.

**Tabla de contenidos**

.. contents::
   :local:


Funcionalidad
=============

Este módulo amplía el modelo ``stock.warehouse.orderpoint`` añadiendo:

* Cálculo automático de la **cantidad mínima basada en el consumo histórico**.
* Configuración del período de cálculo (anual o semestral).
* Cálculo de:

  - Último período (media mensual): puede ser anual o semestral.
  - Último mes.
  - Cantidad sugerida de compra.
  - Cantidad real de compra ajustada a múltiplos de proveedor.

* Acciones masivas mediante asistente para:

  - Copiar sugerencia a cantidad de compra.
  - Actualizar cantidades mín/máx de la regla.
  - Recalcular consumo del período.
  - Generar aprovisionamientos automáticamente.

Además, incluye una tarea programada (cron) que recalcula la cantidad mínima
del último período para todos los puntos de pedido.


Configuración
=============

#. Ir a **Ajustes > Opciones generales > Inventario**.
#. Configurar el campo **Cantidad mínima período**:

   - Anual: calcula el consumo medio mensual de los últimos 12 meses.
   - Semestral: calcula el consumo medio mensual de los últimos 6 meses.

Este parámetro se guarda a nivel de compañía.


Uso
===

Recalcular consumo histórico
----------------------------

Desde la vista de **Reglas de reabastecimiento**:

#. Seleccionar uno o varios puntos de pedido.
#. Ejecutar la acción correspondiente.
#. Elegir la opción **Actualizar cant. mín. periodo anterior**.

Esto calculará la media mensual del consumo según el período configurado.

Actualizar reglas Mín/Máx
-------------------------

Con la opción:

- **Actualizar cant (máx/mín)**

Se establecerá:

- Min Qty = consumo medio del período.
- Max Qty = consumo medio × 2.

Generar sugerencia de compra
----------------------------

El campo **Sugerido** se calcula automáticamente como:

    Consumo medio del período − Stock virtual disponible

Posteriormente puede:

- Copiarse a **Comprar**.
- Ajustarse automáticamente al múltiplo mínimo del proveedor.
- Lanzar la generación de aprovisionamientos.

Generar aprovisionamiento
-------------------------

Mediante la opción:

- **Generar órdenes de aprovisionamiento**

Se ejecuta el proceso estándar de procurement usando la cantidad de compra calculada.


Automatización
==============

El módulo incluye un **cron** que ejecuta periódicamente el recálculo del
consumo medio para todos los puntos de pedido.


Créditos
========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
