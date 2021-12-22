###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    early_discount = fields.Many2one(
        comodel_name='partner.early.payment.discount',
        string='Early payment discount',
    )
