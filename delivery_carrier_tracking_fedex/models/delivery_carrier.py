###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[
            ('fedex', 'FedEx'),
        ],
    )

    def _get_tracking_link_fedex(self, picking):
        if not picking or not picking.carrier_tracking_ref:
            return ''
        carrier_tracking_ref = picking.carrier_tracking_ref
        url = self.env['ir.config_parameter'].sudo().get_param(
            'delivery_carrier.tracking_link.fedex')
        return (
            carrier_tracking_ref and url %
            (carrier_tracking_ref, self.env.lang, self.env.lang) or '')

    def fixed_get_tracking_link(self, picking):
        res = super().fixed_get_tracking_link(picking)
        if self.tracking_method == 'fedex':
            return self._get_tracking_link_fedex(picking)
        return res

    def base_on_rule_get_tracking_link(self, picking):
        res = super().base_on_rule_get_tracking_link(picking)
        if self.tracking_method == 'fedex':
            return self._get_tracking_link_fedex(picking)
        return res
