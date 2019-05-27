###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_method = fields.Selection(
        selection_add=[('correos_express', 'Correos Express')])

    def _get_tracking_link_correos_express(self, picking):
        if not picking or not picking.partner_id:
            return ''
        if not picking.carrier_tracking_ref or not picking.partner_id.zip:
            return ''
        return 'https://s.correosexpress.com/search?s=%s&cp=%s' % (
            picking.carrier_tracking_ref, picking.partner_id.zip)

    def fixed_get_tracking_link(self, picking):
        if self.tracking_method == 'correos_express':
            return self._get_tracking_link_correos_express(picking)
        return self.fixed_get_tracking_link(picking)

    def base_on_rule_get_tracking_link(self, picking):
        if self.tracking_method == 'correos_express':
            return self._get_tracking_link_correos_express(picking)
        return self.base_on_rule_get_tracking_link(picking)
