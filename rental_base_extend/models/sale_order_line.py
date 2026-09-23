###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.tools import str2bool


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    rental_product_domain = fields.Binary(
        compute='_compute_rental_product_domain',
    )

    @api.depends('order_id.is_rental_order')
    def _compute_rental_product_domain(self):
        allow_products = str2bool(
            self.env['ir.config_parameter'].sudo().get_param(
                'rental_base_extend.rental_allow_products', False))
        for line in self:
            line.rental_product_domain = (
                []
                if allow_products or not line.order_id.is_rental_order
                else [('rented_product_id', '!=', False)])

    @api.onchange('order_id')
    def _onchange_order_id_set_rental_default(self):
        for line in self.filtered(lambda record: not record.product_id):
            line.rental = line.order_id.is_rental_order
