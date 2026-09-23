=================================
HR Holidays Public Warning Fix
=================================

Descripción
===========

Evita el warning generado por ``hr_holidays_public`` cuando una llamada
proporciona simultáneamente ``employee_id`` y ``partner_id``.

El comportamiento funcional se mantiene: cuando ambos valores existen,
se utiliza el partner.

Warning original
================

El módulo original generaba el siguiente warning al consultar empleados:

::

    2026-08-12 11:17:01,553 WARNING odoo.addons.hr_holidays_public.models.hr_holidays_public: Both 'employee_id' and 'partner_id' were provided in the method's parameters. Ignoring 'employee_id'.
