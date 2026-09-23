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
    'name': 'Portal stock picking signature',
    'summary': 'Approve stock pickings with signature from portal',
    'category': 'Website',
    'version': '12.0.1.7.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'sale_stock',
        'sale_session',
        'stock',
        'stock_picking_signature',
        'portal',
        'website',
    ],
    'data': [
        'views/portal_signature_template.xml',
        'views/portal_template.xml',
        'views/stock_picking_views.xml',
        'views/web_template.xml',
        'views/website_template.xml',
        'wizards/sale_order_confirm_and_pay.xml',
    ],
}
