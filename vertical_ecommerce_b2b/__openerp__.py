# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2016-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Vertical eCommerce B2B',
    'category': 'Vertical',
    'summary': 'Dependencies addons for B2B eCommerce',
    'version': '8.0.0.1',
    'description': '''
    ''',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'auth_signup_company',
        'website_attributes',
        'website_canonical_url',
        'website_cookie_notice',
        'website_crm',
        'website_crm_privacy_policy',
        'website_files',
        'website_hide_info',
        'website_language_selector',
        'website_legal_page',
        'website_myaccount',
        'website_myaccount_invoice',
        'website_myaccount_sale',
        'website_sale',
        'website_sale_attribute_public_name',
        'website_sale_breadcrumb',
        'website_sale_checkout_comment',
        'website_sale_default_country',
        'website_sale_empty_cart',
        'website_sale_fix_checkout_signin',
        'website_sale_places',
        'website_sale_product_sequences',
        'website_sale_remove_coupon',
        # https://github.com/OCA/e-commerce/pull/139,
        # sustituye a módulo trey-addons website_sale_cart_add_comments
        # 'website_sale_checkout_comment',
        'website_seo',
        'website_seo_url',
        'website_signup_legal_page_required',
        'website_styles_fix',
    ],
    'data': [
    ],
    'installable': True,
}
