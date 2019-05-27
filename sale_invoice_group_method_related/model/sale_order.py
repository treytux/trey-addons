###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_group_method_id = fields.Many2one(
        related='partner_invoice_id.invoice_group_method_id')
