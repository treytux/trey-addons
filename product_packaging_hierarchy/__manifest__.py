##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2022-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
##############################################################################
{
    'name': 'Product packaging hierarchy',
    'summary': '''
    Allows product packaging hierarchy by adding parent and child fields.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Product',
    'version': '16.0.1.0.0',
    'depends': [
        'delivery_package_number',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_package_barcode.xml',
        'views/report_stock_picking_package.xml',
        'views/stock_picking_views.xml',
        'views/stock_quant_package_views.xml',
        'wizards/stock_quant_package_hierarchy.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
