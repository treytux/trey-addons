###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_formed = fields.Boolean(
        string='Formed',
        track_visibility='always',
    )
    picking_type_required_formed = fields.Boolean(
        string='Picking type required formed',
        related='picking_type_id.required_formed',
    )

    def action_done(self):
        for picking in self:
            if not picking.is_formed and (
                    picking.picking_type_id.required_formed):
                raise ValidationError(_(
                    'Cannot validate picking %s without be formed') % (
                        picking.name))
        return super().action_done()

    def _create_backorder(self, backorder_moves=None):
        if backorder_moves is None:
            backorder_moves = []
        backorders = super()._create_backorder(backorder_moves=backorder_moves)
        for backorder in backorders:
            backorder.is_formed = False
        return backorders
