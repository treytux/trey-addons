###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )

    def _process(self, cancel_backorder=False):
        for picking in self.pick_ids:
            if self.carrier_id:
                picking.carrier_id = self.carrier_id.id
            if not picking.carrier_id and not self.carrier_id and (
                    picking.picking_type_id.carrier_required):
                raise ValidationError(_(
                    'Picking must have a carrier assigned to it before '
                    'being validated.'))
        return super()._process(cancel_backorder=cancel_backorder)
