.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================
Email Reminders Cron
====================

Módulo que añade la funcionalidad de enviar recordatorios por email para los
documentos que, econtrandose en un estado o condición definida, no se haya
modificado esta en el tiempo indicado en el recordatorio.


Configuración
=============

La configuración de este módulo se realiza a través del apartado
"Configuración general" de Odoo. Es imprescindible declarar un dominio del
tipo ('state', '=', 'sale') para que funcione correctamente.


Uso
===

El módulo crea una plantilla de email por defecto y un cron que se ejecutará
cada dos días por defecto.
