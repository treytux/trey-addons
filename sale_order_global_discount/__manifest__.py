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
    'name': 'Sale order global discount',
    'summary': 'Global discounts to sale order.',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Sales',
    'version': '12.0.1.4.0',
    'depends': [
        'account',
        'contacts',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_views.xml',
        'views/sale_order_views.xml',
        'views/report_sale_order.xml',
        'views/res_partner_views.xml',
        'views/res_partner_global_discount_views.xml',
        'views/web_template.xml',
    ],
}
