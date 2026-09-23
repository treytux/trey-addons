###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2026-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Stock Picking Analytic From Sale',
    'summary': 'Create analytic account from SO and propagate to pickings',
    'description': '''
Automatically create an analytic account upon each sale order confirmation
and propagate it to outgoing pickings. Includes a wizard to force-assign
an analytic account to already validated pickings that got left without one.
    ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Sales',
    'version': '16.0.1.1.0',
    'license': 'AGPL-3',
    'depends': [
        'analytic',
        'sale',
        'sale_stock',
        'stock',
        'stock_account',
        'stock_picking_analytic_custom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_view.xml',
        'wizards/stock_move_analytic_create_view.xml',
    ],
}
