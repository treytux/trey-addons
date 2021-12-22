##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
import logging

from odoo import SUPERUSER_ID, api

_log = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _log.info('Create barcodes for products without barcodes')
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        products = env['product.product'].search([('barcode', '=', False)])
        products.barcode_set()
