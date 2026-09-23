###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def validate_sale_orders(self):
        for partner in self:
            orders = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('is_risk_sale_order_limit_exceded', '=', True),
                ('state', 'not in', ['sale', 'done', 'cancel']),
            ])
            for order in orders:
                order.action_confirm()
            for child_partner in partner.child_ids:
                child_partner.validate_sale_orders()

    def write(self, vals):
        res = super().write(vals)
        fields_to_check = ['risk_exception', 'credit_limit', 'risk_sale_order',
                           'risk_sale_order_include', 'risk_sale_order_limit']
        if any(field in vals.keys() for field in fields_to_check):
            self.validate_sale_orders()
        return res
