###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[('gls', 'Global Logistics Systems')])

    def _get_tracking_link_gls(self, picking):
        if not picking or not picking.partner_id:
            return ''
        if picking.partner_id.country_id.phone_code == 34:
            url = 'https://m.gls-spain.es/e/%s/%s'
            return (
                (picking.carrier_tracking_ref and picking.partner_id.zip) and
                url % (picking.carrier_tracking_ref, picking.partner_id.zip) or
                '')
        else:
            url = (
                'https://www.gls-spain.es/es/ayuda/seguimiento-envio/?match=%s'
                '&international=1')
            return (
                picking.carrier_tracking_ref and
                url % picking.carrier_tracking_ref or '')

    def fixed_get_tracking_link(self, picking):
        if self.tracking_method == 'gls':
            return self._get_tracking_link_gls(picking)
        return self.fixed_get_tracking_link(picking)

    def base_on_rule_get_tracking_link(self, picking):
        if self.tracking_method == 'gls':
            return self._get_tracking_link_gls(picking)
        return self.base_on_rule_get_tracking_link(picking)
