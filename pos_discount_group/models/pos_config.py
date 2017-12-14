# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    dto_group_id = fields.Many2one(
        comodel_name='discount.partner.group',
        string='Discount Group Default',
        required=True)
