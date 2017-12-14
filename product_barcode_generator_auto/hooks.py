# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import SUPERUSER_ID
from openerp.api import Environment
import logging

_log = logging.getLogger(__name__)


def _post_init_hook(cr, pool):
    env = Environment(cr, SUPERUSER_ID, {})
    products = env['product.product'].search([('ean13', '=', False)])
    _log.info(
        'Generating barcode for %s products without EAN13' % len(products.ids))
    products.generate_ean13()
