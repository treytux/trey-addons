###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_propagated_comment = fields.Text(
        string='Sale Propagated Comment',
        compute='_compute_sale_propagated_comment',
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends('partner_id')
    def _compute_sale_propagated_comment(self):
        for order in self:
            order.sale_propagated_comment = (
                order.partner_id.sale_propagated_comment)
