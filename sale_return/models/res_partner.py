###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_return_count = fields.Integer(
        compute='_compute_sale_order_count',
        string='Default max return days',
    )

    def _compute_sale_order_count(self):
        for partner in self:
            partner.sale_return_count = self.env['sale.order'].search_count([
                ('partner_id', '=', partner.id),
                ('is_return', '=', True),
            ])
