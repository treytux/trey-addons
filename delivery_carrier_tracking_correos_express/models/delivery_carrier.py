###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[
            ('correos_express', 'Correos Express'),
        ],
    )

    def _get_tracking_link_correos_express(self, picking):
        tracking_link = self.env['ir.config_parameter'].sudo().get_param(
            'delivery_carrier.tracking_link.correos_express')
        if (
            not picking or not picking.partner_id
                or '%s' not in tracking_link):
            return ''
        if not picking.carrier_tracking_ref or not picking.partner_id.zip:
            return ''
        return tracking_link % (
            picking.carrier_tracking_ref, picking.partner_id.zip)

    def fixed_get_tracking_link(self, picking):
        res = super().fixed_get_tracking_link(picking)
        if self.tracking_method == 'correos_express':
            return self._get_tracking_link_correos_express(picking)
        return res

    def base_on_rule_get_tracking_link(self, picking):
        res = super().base_on_rule_get_tracking_link(picking)
        if self.tracking_method == 'correos_express':
            return self._get_tracking_link_correos_express(picking)
        return res
