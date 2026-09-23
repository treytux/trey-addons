###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    order_amount_untaxed = fields.Float(
        compute='_compute_order_amount_untaxed',
        string='Sales',
    )

    def _compute_order_amount_untaxed(self):
        for partner in self:
            orders = self.env['sale.order'].search([
                ('partner_id', 'child_of', partner.ids),
            ])
            partner.order_amount_untaxed = sum(
                order.amount_untaxed for order in orders)
