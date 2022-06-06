================
Delivery Correos
================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|
This addon integrates the Correos web services to register a shipment, obtain the tracking ID and the shipping label.

```

**Table of contents**

.. contents::
   :local:

Usage
=====

You have to set Correos carrier in the stock picking you want to ship:

 * In the stock picking form go to *Additional Info* tab and choose Correos as carrier and the service and product code. You only be able to choose this if the state of the picking is 'Ready to Transfer'.

 * When the picking is 'Transferred' the shipping label will be 'attached' and tracking reference will be show in additional info tab.

Autor
~~~~~~~

* `Trey <https://www.trey.es>`_:
