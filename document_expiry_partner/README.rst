.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Document Expiry Partner
=======================

Módulo para gestionar la caducidad de la documentación asociada a los
contactos de Odoo.

Permite registrar documentos personalizados o documentos adjuntos, controlar
sus fechas de validez y recibir actividades cuando están próximos a caducar o
ya han caducado.


Características
===============

* Añade los contactos como propietarios de documentos con fecha de caducidad.
* Permite consultar la documentación desde el formulario del contacto.
* Permite gestionar la documentación desde el menú de caducidad de documentos.
* Clasifica automáticamente los documentos como válidos, próximos a caducar
  o caducados.
* Muestra el estado del documento mediante colores.
* Permite asociar un documento a un fichero adjunto de Odoo.
* Crea actividades sobre el contacto para los usuarios configurados para
  recibir avisos.
* Evita crear actividades duplicadas para el mismo contacto, usuario y tipo
  de actividad.


Configuración
=============

Para recibir avisos de caducidad:

#. Acceda a **Ajustes > Usuarios y compañías > Usuarios**.
#. Abra el usuario que debe recibir los avisos.
#. Active el permiso **Avisar al usuario cuando los documentos de los
   contactos caduquen**.

La acción planificada **Avisar al contacto de la caducidad de la
documentación** revisa diariamente los documentos y crea las actividades
correspondientes.


Uso
===

Desde **Contactos > Contactos**, abra un contacto y acceda a la pestaña
**Documentación**. Desde allí puede crear y editar documentos asociados al
contacto.

Cada documento debe incluir una fecha de inicio anterior o igual a la fecha
de finalización. La fecha de finalización determina el estado del documento:

* **Válido**: la fecha de finalización todavía no está dentro del periodo de
  aviso.
* **Aviso**: el documento se encuentra dentro del periodo configurado para
  avisos.
* **Caducado**: la fecha de finalización ya ha pasado.

También puede consultar todos los documentos de contactos desde
**Caducidad de documentos > Contactos** y agruparlos por contacto desde la
vista de búsqueda.


Seguridad e integridad
======================

La pestaña y los menús de documentación están disponibles para los usuarios
del grupo de usuarios de **Caducidad de documentos**.

Los documentos mantienen una relación restringida con el contacto. Por tanto,
no se puede eliminar un contacto mientras tenga documentación vinculada.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
