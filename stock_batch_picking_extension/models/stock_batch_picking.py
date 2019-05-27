###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api, fields


class StockBatchPicking(models.Model):
    _inherit = 'stock.batch.picking'
    _order = 'id desc'

    picker_id = fields.Many2one(
        default=lambda s: s.env.user.id,
        domain='[("share", "=", False)]')

    @api.multi
    def action_cancel(self):
        for batch in self:
            batch.write({'state': 'cancel'})

    @api.multi
    def action_cancel_to_draft(self):
        for batch in self:
            if batch.state != 'cancel':
                continue
            batch.write({'state': 'draft'})

    @api.multi
    def action_do_print(self):
        pickings = self.env['stock.picking']
        for batch in self:
            for picking in batch.picking_ids:
                pickings |= picking
        return pickings.do_print_picking()
