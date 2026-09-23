============
Delivery DHL
============

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

This addon integrates the DHL web services to register a shipment, obtain the 
tracking ID and the shipping label.::

   Note: "This app is independently developed by Trey and is not affiliated with,
   endorsed by, verified by, certified by, or approved by DHL. DHL is a 
   trademark of DHL International GmbH and is referenced only to describe
   compatibility with DHL services."


**Table of contents**

.. contents::
   :local:

Usage
=====

You have to set DHL carrier in the stock picking you want to ship:

 * In the stock picking form go to *Additional Info* tab and choose DHL as 
   carrier and the service and product code. You only be able to choose this if 
   the state of the picking is 'Ready to Transfer'.

 * When the picking is 'Transferred' the shipping label will be 'attached' and 
   tracking reference will be show in additional info tab.

Author
~~~~~~~

* `Trey <https://www.trey.es>`_
