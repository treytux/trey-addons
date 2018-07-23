# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    role_id = fields.Many2one(
        comodel_name='res.partner.role',
        string='Role',
        required=False)
    model_name = fields.Char(
        related='role_id.model_name')
