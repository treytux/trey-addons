.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================
Mail Thread Default Followers
=============================

Este módulo permite modificar los seguidores que se añaden por defecto en la
creación de los hilos de mensajes asociados en los diferentes modelos.

Uso
===

En los ajustes técnicos de Odoo, dentro de los modelos, podemos elegir
diferentes configuraciones para modificar el comportamiento por defecto de la
agregación de seguidores en la creación registros de estos modelos:

   - Defecto: El sistema actuará por defecto.
   - Ninguno: El sistema no añadirá seguidores en la creación.
   - Propietario: Añade al usuario creador del registro.
   - Propietario y escritores: Añade al usuario creador y a los editores del
   registo.
   - Propietario y empresa: Añade al usuario creador y al partner del registro.


Autor
~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__
