##############################################################################
#
#    Trey (www.trey.es)
#    Copyright (C) 2026-Today Trey (www.trey.es) <www.trey.es>
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
    'name': 'Indian Localization Extended',
    'summary': 'Aggregated extended functionalities for Indian localization',
    'version': '16.0.1.1.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'l10n_in',
        'product_harmonized_system',
        'purchase',
        'sale_management',
    ],
    'data': [
        'data/account_tax_data.xml',
        'views/account_move_views.xml',
        'views/hs_code_views.xml',
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
        'views/res_country_state_views.xml',
        'views/sale_order_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
