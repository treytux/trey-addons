=============================================
Sale order line supplierinfo fix customerinfo
=============================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo corrige el error:

    TypeError: Many2many fields product.customerinfo.route_ids and product.supplierinfo.route_ids use the same table and columns​

que se produce al instalar el módulo "sale_order_line_supplierinfo" junto con
el módulo "product_supplierinfo_for_customer".

Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`__:

~~~~~
