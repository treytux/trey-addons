============================
Partner commercial visibility
============================
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3


* Este módulo permite que los usuarios sólo vean las contactos en las que esté asignado como comercial y sus hijos.
* Para que pueda ver todas las contactos diríjase al usuario y seleccione el grupo "Ver todos las contactos".



 Issues
===========

* Si da error al entrar a presupuestos se necesita modificar el dominio de la regla añadiendo el partner asociado al public user

   ['|','|', '&','|', ('type', '=', False),('type', '!=', 'private'),'|',('user_id', '=', user.id),('id', '=', user.partner_id.id),'&','|', ('commercial_partner_id.type', '=', False),('commercial_partner_id.type', '!=', 'private'),('commercial_partner_id.user_id', '=', user.id),('id', '=', <ID_DEL_PUBLIC_PARTNER>)]

El error sucede ya que al tener el módulo "website_sale" instalado, el carrito de compra utiliza el partner público para gestionar las compras anónimas y si este partner no es visible para el usuario, se produce un error.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
