.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Procurement send exception errors
====

Crea un cron que a diario busca los abastecimientos que están en estado
excepción y envía un correo a los usuarios configurados para tal fin con el
listado de todos ellos para que los revisen.


Configuración:
----

Añadir los usuarios a notificar desde el menú Configuración/Almacén en el
campo "Usuarios que serán informados de los abastecimientos en excepción".


Notas:
----

En un entorno multicompañía, si se ejecuta de forma automática o por el
usuario administrador manualmente, tendrá en cuenta los abastecimientos de
todas las compañías.
Si por el contrario el cron es ejecutado manualmente por algún usuario no
administrador sólo se tendrán en cuenta los abastecimientos de la compañía en
la que esté identificado en ese momento.
