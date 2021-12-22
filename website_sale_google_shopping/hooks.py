###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """
    Import Google Product Taxonomies:
    https://support.google.com/merchants/answer/1705911?hl=en
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # TODO: Allow to choose import lang
        lang = env.context.get('lang', 'en_US')
        category = env['google_product_category']
        path = odoo.modules.module.get_module_path(
            'website_sale_google_shopping')
        taxonomies_file = open(
            path + 'data/taxonomy-with-ids.%s.txt' % lang.replace(
                '_', '-'), 'r')
        if taxonomies_file:
            for line in taxonomies_file:
                data = line.split(' - ')
                if len(data) > 1:
                    category.create({
                        'google_id': data[0],
                        'name': data[1],
                    })
