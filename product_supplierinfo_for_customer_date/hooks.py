# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################


def _post_init_hook(cr, pool):
    cr.execute(
        'UPDATE product_supplierinfo SET date=write_date WHERE date IS NULL')
