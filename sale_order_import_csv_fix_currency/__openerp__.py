# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Sale order import csv fix currency',
    'summary': 'Sale order import csv fix currency',
    'description': '''
Fix the error:

    "The customer 'Customer_name' has a pricelist 'Pricelist pricelist_name
    (CURRENCY)' but the currency of this order is 'OTHER_CURRENCY'."

when trying to import a file using the 'Import RFQ or Order' wizard when the
company has a pricelist with a different currency from the company.
    ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Sales',
    'version': '8.0.0.1.0',
    'depends': [
        'base_business_document_import',
        'sale_order_import_csv',
    ],
    'data': [],
    'installable': True,
}
