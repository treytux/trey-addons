# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResPartnerRole(models.Model):
    _name = 'res.partner.role'
    _order = 'name'

    name = fields.Char(
        string='Role',
        required=True,
        translate=True)
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        required=True)
    model_name = fields.Char(
        related='model_id.model')
