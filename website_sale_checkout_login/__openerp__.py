# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
###############################################################################
{
    'name': 'Checkout Login',
    'category': 'website',
    'summary': 'Add a login page to the process of buying '
    'the online store.',
    'version': '8.0.1.0.0',
    'description': """
    This module depends on auth_oauth, you should check
    your configuration in *Configuration > Users >
    OAuth Providers* and disable the ones you do not need.
    """,
    'author': 'Trey (www.trey.es)',
    'depends': [
        'auth_oauth',
        'website_sale',
        'website_signup_legal_page_required',
    ],
    'data': [
        'views/website_config_setting.xml',
        'views/res_users.xml',
        'templates/website_sale.xml',
        'templates/website_sale_checkout_login.xml',
    ],
    'installable': True,
}
