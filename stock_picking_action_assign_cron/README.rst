================================
Stock picking action assign cron
================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo añade una tarea planificada (*cron*) que ejecuta automáticamente la acción de asignación de stock sobre los albaranes en estado "Confirmado" o "En espera".

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

Una vez instalado, el sistema ejecutará periódicamente un proceso que buscará los albaranes en estado "Confirmado" o "En espera" y tratará de asignarles automáticamente el stock disponible.

No se requiere configuración adicional. La tarea planificada queda instalada y activada por defecto, aunque se puede ajustar su frecuencia desde el menú:

    *Ajustes técnicos > Automatización > Tareas programadas*

Créditos
========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
