# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################


def _post_init_hook(cr, pool):
    cr.execute('''
        UPDATE stock_picking
        SET partner_print_id=partner_id
        WHERE partner_print_id IS NULL''')
