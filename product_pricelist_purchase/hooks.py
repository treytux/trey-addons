##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import logging

_log = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _log.info('Move field price to ref_price in product.supplierinfo model')
    cr.execute('UPDATE product_supplierinfo SET ref_price = price;')


def uninstall_hook(cr, registry):
    _log.info('Move field ref_price to price in product.supplierinfo model')
    cr.execute('UPDATE product_supplierinfo SET price = ref_price;')
