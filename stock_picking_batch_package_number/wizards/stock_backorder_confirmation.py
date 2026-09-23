###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    hide_line_ids = fields.Boolean(
        string='Hide line ids',
        default=True,
    )
    line_ids = fields.One2many(
        comodel_name='stock.backorder.confirmation.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if not self.env.context.get('batch', False):
            return res
        res['hide_line_ids'] = False
        if 'line_ids' not in res:
            res['line_ids'] = []
        batch = self.env.context.get('batch')
        assigned_picking_list = batch.picking_ids.filtered(
            lambda p: p.state == 'assigned').sorted(
                key=lambda r: r.scheduled_date)
        for picking in assigned_picking_list:
            qty_request = sum(
                picking.move_ids_without_package.mapped('product_uom_qty'))
            qty_done = sum(
                picking.move_ids_without_package.mapped('quantity_done'))
            if qty_done == qty_request or (
                    qty_done != 0 and qty_done < qty_request):
                line = {
                    'wizard_id': self.id,
                    'picking_id': picking.id,
                    'number_of_packages': 1,
                }
                res['line_ids'].append((0, 0, line))
        return res

    def _process(self, cancel_backorder=False):
        if self.hide_line_ids:
            return super()._process(cancel_backorder=cancel_backorder)
        for line in self.line_ids:
            line.picking_id.number_of_packages = line.number_of_packages
        return super()._process(cancel_backorder=cancel_backorder)


class StockBackorderConfirmationLine(models.TransientModel):
    _name = 'stock.backorder.confirmation.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.backorder.confirmation',
        string='Wizard',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    number_of_packages = fields.Integer(
        string='Number of packages',
    )
