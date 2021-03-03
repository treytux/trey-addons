###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Stock Alert',
    'summary': 'Create alerts for products without stock',
    'category': 'Website',
    'version': '11.0.1.2.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'sale',
        'website_sale',
    ],
    'data': [
        'data/website_sale_stock_alert_cron.xml',
        'data/website_sale_stock_alert_email.xml',
        'security/ir.model.access.csv',
        'views/product_stock_alert.xml',
        'views/res_partner.xml',
        'views/website.xml',
        'views/website_sale.xml',
    ],
    'installable': True,
}
