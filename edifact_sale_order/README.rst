.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================
Edifact Sale Order
==================

Module for import / export sale orders from edifact files.

@TODO: export sale orders.


Configuration parameters:
=========================

Settings > Companies > Companies > Configuration > EDI parameters

Salesman: sales person for documents
In path: path for import files
Out path: path for exported files

Paths indiqued here must exist in your server.
Inside this paths, you have to create a folder named "orders" for this module.

How it works
============

Importing files:

You have to put import files inside in path > orders.

Manual method: Edifact > Sale Orders > Import Orders
Cron: Settings > Technical > Automation > Schedule Actions > Process EDI order files

Processed documents are located in Edifact > Edifact Documents > Documents, where their state shows if errors have ocurred.

Imported files will be deleted afer their processing.


