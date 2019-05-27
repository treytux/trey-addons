###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_invoice_id = fields.Many2one(
        domain=("['|', ('id', '=', partner_id), '&', "
                "('id', 'child_of', partner_id), ('type', '=', 'invoice')]"))
    partner_shipping_id = fields.Many2one(
        domain=("['|', ('id', '=', partner_id), '&', "
                "('id', 'child_of', partner_id), ('type', '=', 'delivery')]"))
