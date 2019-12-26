.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Mrp check stock availability
====

Check the availability of the consumed products for the movements that are
generated in manufacturing.


Configuration
====

You can configure the type of stock used (real or virtual stock) to take into
account from the Configuration/Companies/Companies menu in the "MRP" section
of the "Configuration" tab.
By default, the virtual stock will be taken into account.


Usage
====

If, when manufacturing, there is no available stock of the configured type, a
warning will be displayed to inform the user and will not allow him to
continue.
