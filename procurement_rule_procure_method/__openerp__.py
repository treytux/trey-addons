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
    'name': 'Procurement rule procure method',
    'summary': 'Procurement rule procure method',
    'description': '''
Add a new procure method 'MTS + MTO' to be selected in the procurement rules so
that, when a stock move is confirmed, it is checked if it is reserved in some
quant. If it is, will change the procure method to 'make_to_stock'. Otherwise,
will change it to 'make_to_order' and reconfirm the move so that the purchase
is created.''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Warehouse',
    'version': '8.0.1.0.0',
    'depends': [
        'procurement',
        'stock',
    ],
    'data': [],
    'installable': True,
}
