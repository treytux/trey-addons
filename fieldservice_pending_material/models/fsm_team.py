###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class FsmTeam(models.Model):
    _inherit = 'fsm.team'

    order_pending_material_count = fields.Integer(
        compute='_compute_order_pending_material_count',
        string='Orders pending',
    )

    @api.depends('order_ids', 'order_ids.pending_material')
    def _compute_order_pending_material_count(self):
        for team in self:
            team.order_pending_material_count = len(
                team.order_ids.filtered(lambda fsm: fsm.pending_material))
