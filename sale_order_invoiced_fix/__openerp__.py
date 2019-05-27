# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Sale order invoiced fix',
    'summary': 'Sale order invoiced fix',
    'description': '''
Casuistry that corrects this module:

Sales order with more than one line and at least one of them with a product of
service type or a description without product. This order has order policy
"On delivery order". When the stock picking is generated, it is partially
transferred in more than one stock picking and, subsequently, those invoices
are invoiced at the same time, the invoices are generated correctly.

But if we now cancel the invoices and re-generate them from the stock pickings,
the product service lines or without product are duplicated, since they appear
in all the generated invoices.
That is, the first time you invoice there is no error, but the following ones.

This module is responsible for solving the error committed by the
"_fnct_line_invoiced" function that calculates the "invoiced" field. For this
we calculate the value of the "invoiced" field from another function that
corrects it.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Sales',
    'version': '8.0.0.1.0',
    'depends': [
        'sale',
    ],
    'data': [],
    'installable': True,
}
