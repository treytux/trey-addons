.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

security
====

Modificaciones realizadas
----

-  Menú "Empleados": sólo los usuarios de los grupos "Empleado/Oficial" o "Empleado/Responsable" podrán verlo.

- Campo "Precio de venta" de los productos (plantillas y variantes): sólo pueden verlo los usuarios que pertenezcan a los grupos "Ventas/Usuario: Mostrar todos los documentos", "Usuario: Solo mostrar documentos propios", "Ventas/Responsable" y "Compras/Responsable".

- Campos "Precio de coste" y "Precio categoría de coste" de los productos (plantillas y variantes): sólo pueden verlo los usuarios que pertenezcan a los grupos "Ventas/Responsable" y "Compras/Responsable".

- Se modifica la regla de registro "base.res_partner_rule_private_employee" para que los usuarios internos sólo tengan acceso a las direcciones no privadas o sin tipo que tengan asignado a si mismo como comercial.

- Se crea un nuevo grupo "Ver todas las empresas" con una regla de registro que permite ver todas las empresas del sistema.
