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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Purchase order lines by ref',
    'summary': 'Wizard to create purchase lines with refs or importing xls',
    'category': 'Purchase',
    'version': '16.0.1.5.1',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/purchase_order_lines_by_ref.xml',
        'wizards/purchase_order_lines_by_ref_xls.xml',
        'views/purchase_order_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
