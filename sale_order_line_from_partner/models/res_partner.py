###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_order_line_count = fields.Integer(
        string='Sale order line count',
        compute='_compute_sale_order_line_count'
    )

    @api.multi
    def _compute_sale_order_line_count(self):
        for partner in self:
            order_lines = self.env['sale.order.line'].search([
                ('order_partner_id', '=', partner.id)])
            partner.sale_order_line_count = len(order_lines)
