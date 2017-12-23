# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Agent Checkout',
    'summary': 'Customized checkout for agents',
    'description': '''Module for agent users that allows to select one of their
    partners in checkout process. When confirmation button is pressed,
    the selected partner and their addresses will be asigned to order.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Website',
    'version': '8.0.0.1.0',
    'depends': [
        'product_season_sale',
        'sale_commission',
        'sale_order_price_recalculation',
        'website_sale',
    ],
    'data': [
        'templates/website.xml',
        'templates/website_sale_checkout_agent.xml',
    ],
    'installable': True,
}
