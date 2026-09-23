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
    'name': 'Connector Woocommerce',
    'summary': 'A simple woocomerce connector',
    'category': 'Sale',
    'version': '12.0.1.43.3',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'base_location',
        'delivery',
        'l10n_es_partner',
        'product',
        'product_template_tags',
        'product_catalog_label',
        'queue_job',
        'sale',
        'sales_team',
        'stock',
        'website_sale',
        'website_sale_description_backend',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/product_product.xml',
        'views/payment_acquirer_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/product_public_category.xml',
        'views/res_config_settings_views.xml',
        'views/website_views.xml',
        'views/website_woo_log_views.xml',
        'views/website_woo_mapp_tax_views.xml',
        'wizards/product_template.xml',
        'wizards/woocommerce_sale_import.xml',
        'wizards/woocommerce_sync.xml',
    ],
    'external_dependencies': {
        'python': ['woocommerce'],
    },
}
