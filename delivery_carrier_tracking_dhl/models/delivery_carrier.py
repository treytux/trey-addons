###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[
            ('dhl', 'DHL'),
            ('dhl_express', 'DHL Express'),
        ],
    )

    def map_tracking_parameter_dhl(self):
        ir_config_obj = self.env['ir.config_parameter']
        return {
            'dhl': ir_config_obj.sudo().get_param(
                'delivery_carrier.tracking_link.dhl'),
            'dhl_express': ir_config_obj.sudo().get_param(
                'delivery_carrier.tracking_link.dhl_express'),
        }

    def _get_tracking_link_dhl(self, picking):
        tracking_url_parameter = self.map_tracking_parameter_dhl().get(
            self.tracking_method, '')
        if (
            not picking or not picking.carrier_tracking_ref
                or tracking_url_parameter.find('%s') == -1):
            return ''
        return tracking_url_parameter % picking.carrier_tracking_ref

    def fixed_get_tracking_link(self, picking):
        res = super().fixed_get_tracking_link(picking)
        if self.tracking_method in ['dhl', 'dhl_express']:
            return self._get_tracking_link_dhl(picking)
        return res

    def base_on_rule_get_tracking_link(self, picking):
        res = super().base_on_rule_get_tracking_link(picking)
        if self.tracking_method in ['dhl', 'dhl_express']:
            return self._get_tracking_link_dhl(picking)
        return res
