.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Edifact Stock Picking
=====================

Module for import / export stock pikings from / to edifact files.

@TODO: import stock picking.


Configuration parameters:
=========================

Settings > Companies > Companies > Configuration > EDI parameters

Salesman: sales person for documents
In path: path for import files
Out path: path for exported files

Paths indiqued here must exist in your server.
Inside this paths, you have to create a folder named "pickings" for this module.

How it works
============

Exporting files:

Edifact > Pickings > Export Pickings

Select pickings to export and click on export button.

Exported files will be inside the configured out path / pickings folder.




