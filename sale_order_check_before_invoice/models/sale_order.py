###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_check_before_invoice = fields.Boolean(
        related='partner_id.check_before_invoice',
        string='Check before invoice',
    )
