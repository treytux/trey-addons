=================================
Helpdesk Ticket Team Multicompany
=================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo permite elegir el dominio del alias de un equipo de helpdesk a
partir de los dominios disponibles en los servidores de correo saliente
configurados.

Uso
---
1. Abra un equipo de helpdesk.
2. En `alias_domain`, seleccione uno de los dominios que aparecen en el
   desplegable.

Comportamiento
--------------

* El campo `alias_domain` se presenta como un desplegable editable.
* Las opciones del desplegable se construyen a partir de los servidores de
  correo activos.
* Para cada servidor se usa primero `from_filter`; si está vacío, se toma el
  dominio del `smtp_user`.
* Si varios servidores apuntan al mismo dominio, se muestra una sola opción.
* Al seleccionar un dominio, el sistema resuelve internamente el servidor SMTP
  asociado y guarda esa referencia en el alias.
* Si no hay servidor asociado al equipo, se mantiene el comportamiento
  estándar y se usa `mail.catchall.domain` como dominio de respaldo.
* Si existe un servidor de la compañía del equipo, se propone como valor por
  defecto al crear el registro.


**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
