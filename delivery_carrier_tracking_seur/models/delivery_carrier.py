###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[('seur', 'SEUR')])

    def _get_tracking_link_seur(self, picking):
        if not picking or not picking.carrier_tracking_ref:
            return ''
        url = 'https://www.seur.com/livetracking/?segOnlineIdentificador=%s'
        return url % picking.carrier_tracking_ref

    def fixed_get_tracking_link(self, picking):
        if self.tracking_method == 'seur':
            return self._get_tracking_link_seur(picking)
        return self.fixed_get_tracking_link(picking)

    def base_on_rule_get_tracking_link(self, picking):
        if self.tracking_method == 'seur':
            return self._get_tracking_link_seur(picking)
        return self.base_on_rule_get_tracking_link(picking)
