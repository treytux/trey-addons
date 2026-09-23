.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock Picking Validate Weight
=============================

Este módulo permite introducir el peso real de un albarán durante su
validación. El peso indicado por el usuario se conserva en el albarán y se
utiliza posteriormente en la información de envío y en el albarán de entrega.

Funcionalidades
===============

* Añade el campo ``Shipping weight validate`` al albarán.
* Muestra el peso calculado inicialmente en los asistentes de transferencia
  inmediata y de confirmación de backorder.
* Permite modificar el peso antes de validar el albarán.
* Guarda el peso validado para evitar que el peso mostrado en el documento de
  entrega se recalcule posteriormente.
* Actualiza el peso utilizado por el transportista cuando se envía el albarán.
* Mantiene el peso validado tanto en validaciones completas como en
  validaciones parciales con backorder.

Uso
===

1. Abra un albarán con productos reservados.
2. Inicie la validación del albarán.
3. En el asistente de transferencia inmediata o de backorder, revise el
   campo ``Total weight``.
4. Introduzca el peso real del envío.
5. Confirme la validación.

El peso introducido se guarda en ``shipping_weight_validate`` y se refleja en
``shipping_weight``. El valor queda disponible para el informe de albarán de
entrega y para las integraciones con transportistas.

Dependencias
============

* ``stock`` — gestión de albaranes y validaciones.
* ``delivery_package_number`` — información adicional del paquete en los
  albaranes de entrega.

Configuración
=============

No requiere configuración adicional. El campo de peso aparece
automáticamente en los asistentes de validación de albaranes.

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

Licencia
========

Este módulo está licenciado bajo AGPL-3.
