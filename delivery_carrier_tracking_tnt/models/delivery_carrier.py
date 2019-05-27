###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[('tnt', 'TNT Express Shipping')])

    def _get_tracking_link_tnt(self, picking):
        if not picking:
            return ''
        url = (
            'https://www.tnt.com/express/es_es/site/herramientas-envio/'
            'seguimiento.html?searchType=ref&cons=%s')
        return (
            picking.carrier_tracking_ref and
            url % picking.carrier_tracking_ref or '')

    def fixed_get_tracking_link(self, picking):
        if self.tracking_method == 'tnt':
            return self._get_tracking_link_tnt(picking)
        return self.fixed_get_tracking_link(picking)

    def base_on_rule_get_tracking_link(self, picking):
        if self.tracking_method == 'tnt':
            return self._get_tracking_link_tnt(picking)
        return self.base_on_rule_get_tracking_link(picking)
