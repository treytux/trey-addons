###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2023-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Stock picking material certificate',
    'summary': (
        'Add material certificate number to lot and modify views for '
        'introduce from incoming picking.'
    ),
    'category': 'Stock',
    'version': '12.0.1.4.1',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'print_formats_base',
        'stock',
    ],
    'data': [
        'views/report_stock_conformity.xml',
        'views/res_company_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_production_lot_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
