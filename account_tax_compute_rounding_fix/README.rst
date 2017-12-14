**Parche** de redondeo en el calculo de los impuestos
=====================================================

En el caso de:

* Definir como método de redondeo del cálculo de impuestos "Redondear
  globalmente"
* Establecer una precision mayor de 4 decimales para "Product Price"

El calculo del importe de los impuestos se redondea de forma erronea.

Esto ocurre por que en la definicion del modelo ```account.tax``` del modulo
**account**, en el método ```compute_all``` se establece por defecto una
precision de 5 digitos en el caso de que el metodo de redondeo sea global.

.. highlight:: python
    @api.v7
    def compute_all(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, force_excluded=False):
        ...
        ...
        ...
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = round(price_unit * quantity, precision)
        ...
        ...



Este parche sustituye por completo el metodo de calculo para cambiar la linea


.. highlight:: python
            tax_compute_precision += 5




Por esta otra

.. highlight:: python
            precision += self.pool.get('decimal.precision').precision_get(
                cr, uid, 'Product Price') + 1



Problemas conocidos / Hoja de ruta
==================================

* Solicitar PR a OCA y Odoo

Créditos
========

Contribudores
-------------

* Trey (http://www.trey.es)
