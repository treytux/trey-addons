###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    hide_line_ids = fields.Boolean(
        string='Hide line ids',
        default=True,
    )
    line_ids = fields.One2many(
        comodel_name='stock.immediate.transfer.line',
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
            line = {
                'wizard_id': self.id,
                'picking_id': picking.id,
                'number_of_packages': 1,
            }
            res['line_ids'].append((0, 0, line))
        return res

    def process(self):
        if self.hide_line_ids:
            return super().process()
        for line in self.line_ids:
            line.picking_id.number_of_packages = line.number_of_packages
        return super().process()


class StockImmediateTransferLine(models.TransientModel):
    _name = 'stock.immediate.transfer.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.immediate.transfer',
        string='Wizard',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    number_of_packages = fields.Integer(
        string='Number of packages',
    )
