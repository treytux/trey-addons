.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================
Account Move Unpaid Reminder
===========================

Este módulo envía recordatorios por correo electrónico a los seguidores de las facturas en estado borrador o publicado que tienen el campo de recordatorio de pago pendiente marcado como True.

**Tabla de contenidos**

.. contents::
   :local:

Características
~~~~~~~~~~~~~~~

* Añade un campo `unpaid_reminder` a las facturas.
* Crea una acción planificada para enviar correos electrónicos de recordatorio a los seguidores de las facturas en estado borrador o publicado con el campo `unpaid_reminder` marcado como True.
* Permite enviar recordatorios manualmente desde el listado de facturas y desde la vista de formulario de una factura.
* Envía notificaciones internas a los usuarios de Odoo cuando se envía un recordatorio.
* Publica un mensaje en el registro de la factura cuando se envía un recordatorio.

Instalación
~~~~~~~~~~~

* Copia la carpeta `account_move_unpaid_reminder` en el directorio de addons de tu instalación de Odoo.
* Reinicia el servidor de Odoo.
* Ve a la interfaz de Odoo, activa el modo desarrollador y actualiza la lista de aplicaciones.
* Instala el módulo `Account Move Unpaid Reminder`.

Autor
~~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__
