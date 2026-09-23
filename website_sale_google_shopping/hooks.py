###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import SUPERUSER_ID, api, tools

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Import Google Product Taxonomies:
    https://support.google.com/merchants/answer/1705911?hl=en
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    lang = env.context.get('lang', 'en_US')
    filename = 'taxonomy-with-ids.%s.txt' % lang.replace('_', '-')
    try:
        file_path = 'website_sale_google_shopping/data/%s' % filename
        with tools.file_open(file_path, 'r') as taxonomies_file:
            categories_to_create = []
            for line in taxonomies_file:
                data = line.strip().split(' - ')
                if len(data) > 1:
                    categories_to_create.append({
                        'google_id': data[0],
                        'name': data[1],
                    })
            if categories_to_create:
                env['google_product_category'].create(categories_to_create)
                _logger.info(
                    f"Google Shopping: {len(categories_to_create)} "
                    f"taxonomies imported."
                )
    except FileNotFoundError:
        _logger.warning(
            f"Google Shopping: Taxonomy file not found for language {lang} "
            f"({filename})"
        )
    except Exception as e:
        _logger.error(
            f"Google Shopping: Error importing taxonomies: {str(e)}"
        )
