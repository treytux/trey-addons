# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, an open source suite of business apps
# This module copyright (C) 2015 bloopark systems (<http://bloopark.de>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'One Step Checkout',
    'category': 'Website',
    'summary': 'Provide an All-In-One Checkout for Your Odoo Customer',
    'version': '8.0.0.1',
    'author': 'Trey (www.trey.es)',
    'website': "https://www.trey.es",
    'license': 'AGPL-3',
    'depends': [
        'root_partner',
        'website_sale',
        # Sustituye a módulo trey-addons website_sale_cart_add_comments
        # https://github.com/OCA/e-commerce/pull/139,
        # 'website_sale_checkout_comment',
        'website_sale_delivery',
    ],
    'data': [
        'security/website_sale_os_checkout.xml',
        'templates/website.xml',
        'templates/website_sale.xml',
        'templates/website_sale_delivery.xml',
        'templates/website_sale_os_checkout.xml',
        'views/res_config.xml',
    ],
    'installable': True,
    'auto_install': False,
}
