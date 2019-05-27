###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[('ups', 'UPS')])

    def _get_tracking_link_ups(self, picking):
        if not picking:
            return ''
        url = 'https://www.ups.com/track?loc=%s&tracknum=%s'
        return (
            picking.carrier_tracking_ref and
            url % (self.env.lang, picking.carrier_tracking_ref) or '')

    def fixed_get_tracking_link(self, picking):
        if self.tracking_method == 'ups':
            return self._get_tracking_link_ups(picking)
        return self.fixed_get_tracking_link(picking)

    def base_on_rule_get_tracking_link(self, picking):
        if self.tracking_method == 'ups':
            return self._get_tracking_link_ups(picking)
        return self.base_on_rule_get_tracking_link(picking)
