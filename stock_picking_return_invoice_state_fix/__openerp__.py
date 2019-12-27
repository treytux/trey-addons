# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Stock picking return invoice state fix',
    'summary': 'Stock picking return invoice state fix',
    'description': '''
Solve follow error in stock picking return:
When from a stock picking, click on the button 'Reverse Transfer' to make a
return and yo select any option in the 'Invoice state' field, this field is not
used, the original stock picking is used and this is not correct.''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Warehouse',
    'version': '8.0.1.0.0',
    'depends': [
        'stock_account',
    ],
    'data': [],
    'installable': True,
}
