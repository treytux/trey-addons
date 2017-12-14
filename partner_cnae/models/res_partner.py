# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    cnae = fields.Many2one(
        comodel_name='partner_cnae.cnae',
        string='CNAE'
    )
