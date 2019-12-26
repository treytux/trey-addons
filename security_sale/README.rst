.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

security_sale
====

Modificaciones realizadas
----

- Menú "Ventas/A facturar/Pedidos a Facturar": sólo los usuarios responsables
de ventas tendrán acceso.

- Menú "Ventas/Productos/Tarifas": sólo los usuarios responsables de ventas
tendrán acceso.

Nota
----

Hay que tener en cuenta que estas reglas se aplicarán siempre que el usuario en
cuestión pertenezca a los grupos de usuario, no a los grupos de responsable,
ya que éstos últimos añaden permisos que inhabilitan las reglas de este módulo.
