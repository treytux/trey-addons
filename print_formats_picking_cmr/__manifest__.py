###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2020-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Print Formats Picking CMR',
    'summary': 'CMR Report from Picking',
    'version': '12.0.1.0.0',
    'category': 'Warehouse Management',
    'website': 'https://www.trey.es',
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'web',
    ],
    'data': [
        'data/report_paperformat.xml',
        'views/report_cmr.xml',
        'views/stock_picking_views.xml',
    ],
    'application': True,
}
