###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    margin_percent = fields.Float(
        inverse='_inverse_margin_percent',
    )

    def _update_margin_percent(self):
        for line in self:
            if not line.purchase_price:
                continue
            if not line.margin_percent:
                continue
            if line.margin_percent < 0.000001:
                continue
            if line.margin_percent > 0.999999:
                raise exceptions.ValidationError(
                    _('Margin percent must be less than 100%.'))
            line.price_unit = (
                line.purchase_price / (1 - line.margin_percent)
            )

    @api.onchange('margin_percent')
    def onchange_margin_percent(self):
        self._update_margin_percent()

    def _inverse_margin_percent(self):
        self._update_margin_percent()
