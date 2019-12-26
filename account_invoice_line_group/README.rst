==========================
Account Invoice Line Group
==========================

Se ha creado un nuevo modelo account.invoice.line.group con los campos:

**state**:

- *draft* (que no se ha asignado a ninguna factura)
- *no-editable* (que ya se ha asignado la agrupación en una linea de factura
  validada)

**name**:

- nombre corto del concepto

**description**:

- descripción que se desea mostrar en la impresión

**quantity_method**:

forma de mostrar las cantidades, y sus valores pueden ser:

- *real*: suma el campo product_uom_qty de las lineas
- *fixed*: introduce un valor de cantidad (requiere de otro campo en el modelo)
- *one* (por defecto): muestra valor 1

En las líneas de las facturas, se ha añadido un campo group_id para que el
usuario pueda seleccionar en cada linea por que concepto quiere agrupar.

Se ha modificado el informe de impresión, cuidado que tiene que ser compatible
con nuestro módulo **print_formats_account**

A tener en cuenta....

* Los descuentos en las líneas agrupadas. En la impresión hay que recalcular
  los descuentos, sumando todos los de la misma agrupación y calculando su
  regla de 3.
* La cantidad, dependiendo del método del grupo.
* El orden de las líneas al imprimir. Se imprime en el orden del campo sequence
  de account.invoice.line y cuando se encuentra una línea con agrupación, se
  agrupan todas las líneas con el mismo grupo y se imprime en esta posición,
  siempre que esta agrupación no se haya impreso anteriormente.
* Las agrupaciones se pueden reutilizar entre facturas.


Credits
=======

Authors
~~~~~~~

* Trey, Kilobytes de Soluciones

Contributors
~~~~~~~~~~~~

* Vicent Cubells <vicent@trey.es>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/account-invoicing <https://github.com/OCA/account-invoicing/tree/12.0/account_invoice_cumulative_discount>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
