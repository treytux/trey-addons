###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2021-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Sale Return Historical',
    'summary': 'Allow returns of orders',
    'category': 'Sale',
    'version': '12.0.2.2.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'portal',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat.xml',
        'data/sale_return_historical_email.xml',
        'views/report_print_return_label.xml',
        'views/sale_order_historical_line_views.xml',
        'views/sale_order_historical_views.xml',
        'views/sale_order_template.xml',
        'views/sale_return_historical_template.xml',
    ],
}
