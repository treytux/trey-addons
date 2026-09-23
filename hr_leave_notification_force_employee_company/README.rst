============================================
HR leave notification force employee company
============================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Descripción
===========

Este módulo fuerza el uso de la compañía del empleado en las notificaciones
por correo de ausencias.

Cuando Odoo renderiza una notificación de ``hr.leave``, la cabecera del correo
usa la compañía de ``employee_company_id`` para mostrar el logo, nombre y datos
de contacto correspondientes, en lugar de basarse en la compañía del entorno
(self.env.company).

Uso
---

Instalando el módulo, las notificaciones generadas desde ausencias usan la
compañía del empleado de la ausencia sin cambiar la lógica general de correo
del resto de modelos.
