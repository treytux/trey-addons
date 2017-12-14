# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    auto_invoice = fields.Boolean(
        string='Create auto invoice when pay order')
