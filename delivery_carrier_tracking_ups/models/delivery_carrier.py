###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[
            ('ups', 'UPS'),
        ],
    )

    def _get_tracking_link_ups(self, picking):
        tracking_link = self.env['ir.config_parameter'].sudo().get_param(
            'delivery_carrier.tracking_link.ups')
        if (
            not picking or not picking.carrier_tracking_ref
                or '%s' not in tracking_link):
            return ''
        return (
            picking.carrier_tracking_ref and tracking_link %
            (self.env.lang, picking.carrier_tracking_ref) or '')

    def fixed_get_tracking_link(self, picking):
        res = super().fixed_get_tracking_link(picking)
        if self.tracking_method == 'ups':
            return self._get_tracking_link_ups(picking)
        return res

    def base_on_rule_get_tracking_link(self, picking):
        res = super().base_on_rule_get_tracking_link(picking)
        if self.tracking_method == 'ups':
            return self._get_tracking_link_ups(picking)
        return res
