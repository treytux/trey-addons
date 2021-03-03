###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
    )
