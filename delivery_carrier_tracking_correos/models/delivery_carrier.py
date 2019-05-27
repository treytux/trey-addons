###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[('correos', 'Correos')])

    def _get_tracking_link_correos(self, picking):
        if not picking:
            return ''
        url = 'http://www.correos.es/comun/localizador/track.asp?numero=%s'
        return (
            picking.carrier_tracking_ref and
            url % picking.carrier_tracking_ref or '')

    def fixed_get_tracking_link(self, picking):
        if self.tracking_method == 'correos':
            return self._get_tracking_link_correos(picking)
        return self.fixed_get_tracking_link(picking)

    def base_on_rule_get_tracking_link(self, picking):
        if self.tracking_method == 'correos':
            return self._get_tracking_link_correos(picking)
        return self.base_on_rule_get_tracking_link(picking)
