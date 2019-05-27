###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[('fedex', 'FedEx')])

    def _get_tracking_link_fedex(self, picking):
        if not picking:
            return ''
        url = (
            'https://www.fedex.com/apps/fedextrack/?action=track&'
            'trackingnumber=%s&cntry_code=%s&locale=%s')
        return (
            picking.carrier_tracking_ref and
            url % (
                picking.carrier_tracking_ref,
                self.env.lang, self.env.lang) or '')

    def fixed_get_tracking_link(self, picking):
        if self.tracking_method == 'fedex':
            return self._get_tracking_link_fedex(picking)
        return self.fixed_get_tracking_link(picking)

    def base_on_rule_get_tracking_link(self, picking):
        if self.tracking_method == 'fedex':
            return self._get_tracking_link_fedex(picking)
        return self.base_on_rule_get_tracking_link(picking)
