# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season')
