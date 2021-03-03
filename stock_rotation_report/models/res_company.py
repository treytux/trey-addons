# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_stock_rotation = fields.Boolean(
        string='Calculate stock rotation',
    )
    rotation_init_date = fields.Date(
        string='Rotation init date',
    )
