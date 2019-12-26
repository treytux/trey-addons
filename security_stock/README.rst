.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

security_stock
====

- Se añaden reglas de seguridad asociadas para que los usuarios del nuevo grupo
"Ver sólo objetos relacionados con mis almacenes" sólo vean:

    - Sus almacenes.

    - Los tipos de albarán de sus almacenes.

    - Los albaranes de sus almacenes.

    - Las reglas de abastecimiento de sus almacenes.

    - Las ubicaciones seleccionadas.

    - Los inventarios de las ubicaciones seleccionadas.

- Hacer que el menú "Inventario/Operaciones/Ajustes de inventario" sólo sea
visible para el grupo "Inventario/Responsable"


Configuración
----

- Cada usuario debe tener configurado al menos un almacén y sus ubicaciones
correspondientes. Esta configuración se puede hacer desde la pestaña
"Preferencias" del formulario del usuario, en los campos "Almacenes" y
"Ubicaciones".

- Para que un usuario sólo vea los objetos relacionados con su almacén además
debe pertenecer al grupo "Ver sólo objetos relacionados con mis almacenes".

Nota
----

Hay que tener en cuenta que estas reglas se aplicarán siempre que el usuario en
cuestión pertenezca a los grupos de usuario, no a los grupos de responsable,
ya que éstos últimos añaden permisos que inhabilitan las reglas de este módulo.

