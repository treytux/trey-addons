###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[
            ('gls', 'Global Logistics Systems'),
        ],
    )

    def _get_tracking_link_gls(self, picking):
        url_spain = self.env['ir.config_parameter'].sudo().get_param(
            'delivery_carrier.tracking_link.gls_spain')
        url_int = self.env['ir.config_parameter'].sudo().get_param(
            'delivery_carrier.tracking_link.gls_international')
        partner_id = picking.partner_id
        carrier_tracking_ref = picking.carrier_tracking_ref
        if (
            not picking or not partner_id
                or '%s' not in url_spain or '%s' not in url_int):
            return ''
        if partner_id.country_id.phone_code == 34:
            return (
                (carrier_tracking_ref and partner_id.zip) and url_spain %
                (carrier_tracking_ref, partner_id.zip) or '')
        else:
            return (
                carrier_tracking_ref and url_int % carrier_tracking_ref or '')

    def fixed_get_tracking_link(self, picking):
        res = super().fixed_get_tracking_link(picking)
        if self.tracking_method == 'gls':
            return self._get_tracking_link_gls(picking)
        return res

    def base_on_rule_get_tracking_link(self, picking):
        res = super().base_on_rule_get_tracking_link(picking)
        if self.tracking_method == 'gls':
            return self._get_tracking_link_gls(picking)
        return res
