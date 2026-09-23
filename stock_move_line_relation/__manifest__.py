###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2024-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
###############################################################################
{
    'name': 'Stock move line relation',
    'summary': (
        'Adds a relationship between an out stock movement line with related '
        'input stock movement lines'
    ),
    'category': 'Stock',
    'version': '12.0.1.3.6',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'sale_stock',
        'stock',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_line_relation_views.xml',
        'views/stock_move_line_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
