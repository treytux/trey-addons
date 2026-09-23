###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_domain_carrier_id(self):
        params = self.env.context.get('params')
        if not params or not params.get('id'):
            return []
        if params.get('model') != 'stock.picking':
            return []
        picking = self.env['stock.picking'].browse(params.get('id'))
        return [
            ('id', 'not in', picking.picking_type_id.forbidden_carriers.ids),
        ]

    carrier_id = fields.Many2one(
        domain=_get_domain_carrier_id,
    )

    def button_validate(self):
        self.ensure_one()
        if not self.carrier_id or self.carrier_id == self.sale_id.carrier_id:
            return super().button_validate()
        if self.carrier_id.id not in (
                self.picking_type_id.forbidden_carriers.ids):
            return super().button_validate()
        raise ValidationError(_(
            'The selected carrier is on the list of forbidden carriers for '
            'this picking type.'))
