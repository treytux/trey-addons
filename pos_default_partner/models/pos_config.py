# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default partner')
