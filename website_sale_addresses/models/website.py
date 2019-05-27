###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def _prepare_sale_order_values(self, partner, pricelist):
        vals = super()._prepare_sale_order_values(partner, pricelist)
        shipping = self.env['res.partner'].browse(vals['partner_shipping_id'])
        if shipping.type != 'delivery' and shipping.company_type != 'company':
            vals['partner_shipping_id'] = shipping.commercial_partner_id.id
        return vals
