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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Stock picking edit number',
    'summary': 'Allow to set number and date in stock pickings.',
    'category': 'Stock',
    'version': '16.0.1.1.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'stock_account',
    ],
    'data': [
        'data/res_groups.xml',
        'security/ir.model.access.csv',
        'wizards/stock_picking_edit_wizard.xml',
        'views/stock_picking_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
