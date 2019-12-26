# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


def post_init_hook(cr, registry):
    cr.execute(
        'update res_partner set registration_date = create_date')
