=====================
Print Formats Account
=====================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo nos permite agrupar las líneas de factura según el documento de
origen, ya sea albarán o pedido. También oculta las columnas "Impuestos" y
"Cantidad", esta última solo en el caso de que en todas las líneas la cantidad
sea 1.

**Tabla de contenidos**

.. contents::
   :local:

Configuración
=============

#. En *Contabilidad > Configuración* bajamos hasta la sección "Facturas".
#. Seleccionamos en "Facturas agrupadas por", "Albarán" o "Pedido".
- También podemos cambiar esta opción en:
    *Ajustes > Compañías > La Compañía > Facturas agrupadas por*
#. En *Contabilidad > Configuración > Modos de pago* tenemos que introducir en
el campo "Notas" la descripción, por ejemplo para "Transferencia bancaria"
pondríamos en "Notas": "Transferencia: número de cuenta del banco"

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_
