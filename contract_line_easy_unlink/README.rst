=========================
Contract Line Easy Unlink
=========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Descripción
===========

Este módulo extiende el modelo ``contract.line`` para permitir la cancelación
controlada de líneas de contrato al ser eliminadas desde la interfaz o mediante scripts.

Características Principales
===========================

* Añade método ``cancel()`` para anular líneas de contrato con trazabilidad.
* Añade método ``stop(date_end, manual_renew_needed, post_message)`` que cancela automáticamente las líneas.
* Sobrescribe ``unlink()`` para evitar borrados sin cancelar previamente.
* Publica mensajes en el chatter del contrato indicando qué productos fueron cancelados.

Configuración
=============

Este módulo no requiere configuración adicional después de la instalación.

Uso
===

1. Al eliminar manualmente una línea de contrato desde el backend, esta será automáticamente cancelada antes de ser eliminada.
2. Se asegura que los vínculos de sucesión se limpien correctamente (`predecessor_contract_line_id` / `successor_contract_line_id`).
3. El contrato recibirá un mensaje detallando las líneas canceladas.

Errores Conocidos / Problemas
=============================

* Ninguno por el momento.

Contribuciones
==============

Puedes contribuir mediante issues o pull requests en el repositorio Git (si aplica).

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_

Mantenedores
============

Este módulo es mantenido por:

* Trey (Kilobytes de Soluciones)
