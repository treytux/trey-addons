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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Odoo ecommerce boilerplate',
    'category': 'website',
    'summary': 'Módulo base para implantación de Odoo ecommerce',
    'version': '8.0.0.1',
    'description': '''
    Módulo base para implantación de Odoo ecommerce que incluye las
    dependencias necesarias para la utilización de utilidades y widgets.
    ''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        # 'payment_direct_order',
        # 'sale_stock',
        # 'stock_account',
        # 'website_crm', # Formulario contacto
        # 'website_improvements',
        # 'website_sale_cart_add_comments',
        # 'website_sale_fix_i10n',
        # 'website_sale_product_in_stock',
        # 'website_sale_products_nav',
        'account',
        'auth_signup_force_email',
        'base',
        'clear',
        'l10n_es',
        'purchase',
        'report',
        'sale',
        'stock',
        'website',
        'website_blog',
        'website_blog_url_friendly',
        'website_cookies_policy',
        'website_myaccount',
        'website_myaccount_invoicing',
        'website_order_confirm',
        'website_ratings',
        'website_sale',
        'website_sale_checkout_login',
        'website_sale_delivery',
        'website_sale_product_gallery',
        'website_sale_product_public_name',
        'website_sale_product_sequences',
        'website_sale_products_per_page',
        'website_sale_terms',
        'website_sale_url_friendly',
        'website_sale_vat_helper',
        'website_sale_wishlist',
        'website_seo',
        'website_social_share',
        'website_sale_places_alphabetical'
    ],
    'data': [
        'views/theme.xml',
        'views/shop-category.xml',
        'views/shop-product.xml',

        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        # # 'views/sale_stock_view.xml',  # testing, no activar
        # # 'views/res_config.xml', # pasar a website_improvements
        # 'views/theme.xml',
        # 'views/product-categories.xml',
        # 'views/product.xml',
        # 'views/cart.xml',
        # 'views/res_partner.xml',
        # 'views/menu.xml',
    ],
    'auto_install': False,
    'installable': True,
}
