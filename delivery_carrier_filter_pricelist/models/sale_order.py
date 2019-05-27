###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_shipping_country_id = fields.Many2one(
        related='partner_shipping_id.country_id')
    partner_shipping_state_id = fields.Many2one(
        related='partner_shipping_id.state_id')
    carrier_id = fields.Many2one(
        domain=('''[
            '|',
            ('country_ids', '=', False),
            ('country_ids', 'in', partner_shipping_country_id),
            '|',
            ('state_ids', '=', False),
            ('state_ids', 'in', partner_shipping_state_id),
            '|',
            ('pricelist_id', '=', False),
            ('pricelist_id', '=', pricelist_id)]
            '''))
