# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'
    _inherits = {'repair.workorder': 'workorder_id'}

    workorder_id = fields.Many2one(
        comodel_name='repair.workorder',
        ondelete='cascade',
        string='Work order'
    )
