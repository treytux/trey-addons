.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Report Print Log
===============================

Módulo que añade trazabilidad en la impresión de informes (reports),
registrando en los logs del sistema el usuario que solicita la impresión y el
reporte que se está generando.

Funcionalidad
-------------

- Registra en los logs de Odoo cada vez que se solicita la impresión de un report.
- Muestra información del usuario (nombre, login e ID).
- Muestra información del informe (nombre visible y nombre técnico).
- El log se genera **antes de ejecutar la generación del PDF**.
- En caso de error durante la generación del report, se registra el error junto al usuario e informe.

Uso
---

1. Ir a cualquier aplicación que permita imprimir informes (Ventas, Facturación, Inventario, etc.).
2. Imprimir cualquier reporte.
3. Revisar los logs del servidor de Odoo.
4. Se mostrará una línea con:
   - Usuario que ha solicitado el reporte
   - Reporte que se está generando
   - En caso de error, se mostrará el motivo del fallo, y el usuario e informe.
