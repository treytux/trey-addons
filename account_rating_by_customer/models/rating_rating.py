###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Rating(models.Model):
    _inherit = 'rating.rating'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
    )
