# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################


def migrate(cr, version):
    cr.execute('''
        ALTER TABLE booking
        RENAME COLUMN amount_cost TO amount_cost_gross
    ''')
    cr.execute('''
        ALTER TABLE booking_line
        RENAME COLUMN cost_amount TO cost_net
    ''')
