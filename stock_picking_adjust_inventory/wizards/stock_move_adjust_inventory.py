###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models, tools


class StockMoveAdjustInventory(models.TransientModel):
    _name = 'stock.move.adjust_inventory'
    _description = 'Wizard to adjust inventory from stock.move'

    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Move',
    )
    product_id = fields.Many2one(
        related='move_id.product_id',
        readonly=True,
    )
    location_id = fields.Many2one(
        string='Location',
        related='move_id.location_id',
        readonly=True,
    )
    quantity = fields.Float(
        string='Quantity',
        compute='_compute_quantity',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['move_id'] = self._context.get('active_id')
        return res

    @api.depends('move_id', 'move_id.state', 'move_id.reserved_availability')
    def _compute_quantity(self):
        for adjust in self:
            move = adjust.move_id
            adjust.quantity = move.product_uom_qty - move.reserved_availability

    def action_adjust(self):
        self.ensure_one()
        if self.quantity == 0:
            return
        product = self.product_id.with_context(location=self.location_id.id)
        th_qty = product.qty_available
        inventory = self.env['stock.inventory'].create({
            'name': _('INV: %s') % tools.ustr(self.product_id.display_name),
            'filter': 'product',
            'product_id': self.product_id.id,
            'location_id': self.location_id.id,
            'line_ids': [
                (0, 0, {
                    'location_id': self.location_id.id,
                    'product_id': self.product_id.id,
                    'product_uom_id': self.product_id.uom_id.id,
                    'product_qty': th_qty + self.quantity,
                    'theoretical_qty': th_qty,
                }),
            ],
        })
        inventory.action_validate()
        self.move_id._action_assign()
        return {'type': 'ir.actions.act_window_close'}
