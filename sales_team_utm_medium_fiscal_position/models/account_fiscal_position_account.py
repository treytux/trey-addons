###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountFiscalPositionAccount(models.Model):
    _inherit = 'account.fiscal.position.account'

    medium_id = fields.Many2one(
        comodel_name='utm.medium',
        string='Marketing Medium',
    )
