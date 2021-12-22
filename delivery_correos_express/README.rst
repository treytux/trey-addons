========================
Delivery Correos Express
========================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|
This addon integrates the Correos Express web services to register a shipment, obtain the tracking ID and the shipping label.

With the actual API (June 2021) it is not possible to cancel a shipment,  as confirmed by Correos Express technical department.```

**Table of contents**

.. contents::
   :local:

Usage
=====

You have to set Correos Express carrier in the stock picking you want to ship:

 * In the stock picking form go to *Additional Info* tab and choose Seur as carrier and the service and product code. You only be able to choose this if the state of the picking is 'Ready to Transfer.

 * When the picking is 'Transferred', it appears a *Create Shipping Label* button. Just push it, and if all went well the label will be 'attached'

Autor
~~~~~~~

* `Trey <https://www.trey.es>`_:
