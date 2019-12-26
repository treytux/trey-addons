.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

security_pos
====

Se añaden reglas de seguridad asociadas para que los usuarios del nuevo grupo
"Ver sólo objetos relacionados con mis TPVs" sólo vean:

    - Sus TPVs.

    - Sus pedidos de TPV.

Configuración
----

- Cada usuario debe tener configurado al menos un TPV. Esta configuración se
puede hacer desde la pestaña "Preferencias" del formulario del usuario, en el
campo "TPVs".

- Para que un usuario sólo vea los objetos relacionados con su TPV además
debe pertenecer al grupo "Ver sólo objetos relacionados con mis TPVs".

Nota
----

Hay que tener en cuenta que estas reglas se aplicarán siempre que el usuario en
cuestión pertenezca a los grupos de usuario, no a los grupos de responsable,
ya que éstos últimos añaden permisos que inhabilitan las reglas de este módulo.

