###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class FsmOrder(models.Model):
    _inherit = 'fsm.order'

    pending_material = fields.Boolean(
        string='Pending material',
        compute='_compute_pending_material',
        store=True,
    )

    @api.depends('move_ids', 'move_ids.state')
    def _compute_pending_material(self):
        for fsm_order in self:
            fsm_order.pending_material = False
            if not fsm_order.move_ids:
                continue
            moves_out = fsm_order.move_ids.filtered(
                lambda m: m.picking_code == 'outgoing')
            moves_out_states = list(set(moves_out.mapped('state')))
            fsm_order.pending_material = (
                moves_out and moves_out_states in [['waiting'], ['confirmed']])
