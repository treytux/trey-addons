###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPickingModifyQtyDone(models.TransientModel):
    _name = 'stock.picking.modify_qty_done'
    _description = 'Stock picking modify qty done wizard'

    name = fields.Char(
        string='Empty',
    )
    line_ids = fields.One2many(
        comodel_name='stock.picking.modify_qty_done.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        picking = self.env['stock.picking'].browse(
            self.env.context['active_id'])
        lines = self.env['stock.picking.modify_qty_done.line']
        for move in picking.move_lines:
            lines |= self.env['stock.picking.modify_qty_done.line'].create({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'product_uom_qty': move.product_uom_qty,
                'reserved_availability': move.reserved_availability,
                'quantity_done': move.quantity_done,
            })
        res['line_ids'] = [(6, 0, lines.ids)]
        return res

    def action_all_to_zero(self):
        self.mapped('line_ids').write({
            'quantity_done': 0,
        })
        return self._reopen_view()

    def action_all_to_reserved(self):
        for line in self.line_ids:
            line.quantity_done = line.reserved_availability
        return self._reopen_view()

    def action_all_to_necessary(self):
        for line in self.line_ids:
            line.quantity_done = line.product_uom_qty
        return self._reopen_view()

    def action_modify_qty_done(self):
        for wizard_line in self.line_ids:
            wizard_line.move_id.quantity_done = wizard_line.quantity_done

    def _reopen_view(self):
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking.modify_qty_done',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class StockPickingModifyQtyDoneLine(models.TransientModel):
    _name = 'stock.picking.modify_qty_done.line'
    _description = 'Wizard line'

    name = fields.Char(
        string='Empty',
    )
    wizard_id = fields.Many2one(
        comodel_name='stock.picking.modify_qty_done',
        string='Wizard',
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock move',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    product_uom_qty = fields.Float(
        string='Initial demand',
        readonly=True,
    )
    reserved_availability = fields.Float(
        string='Reserved',
        readonly=True,
    )
    quantity_done = fields.Float(
        string='Done',
    )
