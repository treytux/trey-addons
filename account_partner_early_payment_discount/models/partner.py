###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    early_discount = fields.Float(
        string='% Early Payment Discount',
        help='Early Payment Discount in %.')
