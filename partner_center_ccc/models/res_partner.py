# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    ccc = fields.Char(
        string='CCC'
    )
    workers_number = fields.Integer(
        string='Workers number'
    )
    legal_representative_id = fields.Many2one(
        comodel_name='res.partner',
        string='Legal representative',
        domain=[
            ('is_company', '=', False),
            ('child_ids', '=', None),
            ('is_center', '=', False)])
