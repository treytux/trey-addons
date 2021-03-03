###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[
            ('integrados', 'Integra2'),
        ],
    )

    def _get_tracking_link_integrados(self, picking):
        if not picking or not picking.carrier_tracking_ref:
            return ''
        zip = (
            picking.sale_id
            and picking.sale_id.partner_shipping_id.zip
            and picking.sale_id.partner_shipping_id.zip or (
                picking.partner_id.zip
                and picking.partner_id.zip or ''))
        partner = self.env.user.partner_id
        lang = partner.lang and partner.lang.replace('_', '') or ''
        return self.env['ir.config_parameter'].sudo().get_param(
            'delivery_carrier.tracking_link.integrados') % (
            picking.carrier_tracking_ref, zip[:3], lang)

    def fixed_get_tracking_link(self, picking):
        res = super().fixed_get_tracking_link(picking)
        if self.tracking_method == 'integrados':
            return self._get_tracking_link_integrados(picking)
        return res

    def base_on_rule_get_tracking_link(self, picking):
        res = super().base_on_rule_get_tracking_link(picking)
        if self.tracking_method == 'integrados':
            return self._get_tracking_link_integrados(picking)
        return res
