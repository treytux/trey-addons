# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################


def migrate(cr, version):
    if not version:
        return
    cr.execute('''UPDATE booking as b
                   SET amount_cost_net=
                      (SELECT SUM(cost_net) from booking_line
                         WHERE booking_id =  b.id);''')
