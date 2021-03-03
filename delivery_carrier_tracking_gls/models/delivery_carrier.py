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
        if not picking or not picking.partner_id:
            return ''
        carrier_tracking_ref = picking.carrier_tracking_ref
        if picking.partner_id.country_id.phone_code == 34:
            url = self.env['ir.config_parameter'].sudo().get_param(
                'delivery_carrier.tracking_link.gls_spain')
            return (
                (carrier_tracking_ref and picking.partner_id.zip) and url %
                (carrier_tracking_ref, picking.partner_id.zip) or '')
        else:
            url = self.env['ir.config_parameter'].sudo().get_param(
                'delivery_carrier.tracking_link.gls_international')
            return (
                picking.carrier_tracking_ref and url
                % picking.carrier_tracking_ref or '')

    def fixed_get_tracking_link(self, picking):
        res = super().fixed_get_tracking_link(picking)
        if self.tracking_method == 'gls':
            return self._get_tracking_link_correos(picking)
        return res

    def base_on_rule_get_tracking_link(self, picking):
        res = super().base_on_rule_get_tracking_link(picking)
        if self.tracking_method == 'gls':
            return self._get_tracking_link_gls(picking)
        return res
