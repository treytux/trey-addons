###############################################################################
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
###############################################################################
{
    'name': 'Stock package dummy',
    'summary': 'Generate package labels dummy with barcodes uniques.',
    'category': 'Stock',
    'version': '12.0.1.6.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'stock',
    ],
    'external_dependencies': {
        'python': ['checkdigit'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'data/report_paperformat.xml',
        'views/report_stock_package_dummy_label.xml',
        'views/stock_package_dummy_views.xml',
        'views/stock_picking_views.xml',
        'views/web_template.xml',
        'wizards/stock_package_dummy_read.xml',
        'wizards/stock_package_dummy_print.xml',
    ],
}
