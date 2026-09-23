.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
==============================
Account move line from invoice
==============================

Añade un nuevo botón en el formulario de facturas (cliente y proveedor) para
mostrar el listado de sus líneas comerciales (las de la pestaña de factura),
filtrado por la propia factura. El listado muestra solo esas líneas, sin el
impuesto ni la línea de contrapartida a cobrar/pagar, de modo que coincide con
el contador del botón. Desde ese listado se pueden crear nuevas líneas o
importarlas desde un fichero Excel/CSV.

Sigue el mismo patrón que el módulo ``account_move_line_from_partner``, pero
partiendo de la factura en lugar de la ficha de empresa.

Para que el botón "Importar" aparezca al abrir el listado, el usuario debe
tener permiso de creación sobre ``account.move.line`` (grupo Facturación o
Contabilidad) y, si el módulo ``base_import_security_group`` está instalado,
pertenecer además al grupo "Import CSV/Excel files". Esto es una condición
de seguridad de usuario, no del módulo.
