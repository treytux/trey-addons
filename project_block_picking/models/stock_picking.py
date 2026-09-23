###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        index=True,
    )
    picking_blocked = fields.Boolean(
        string='Picking blocked',
        compute='_compute_picking_blocked',
        compute_sudo=True,
        help='Stock moves cannot be added or edited when the linked task is '
             'blocked or its project blocks pickings, is archived or is in a '
             'folded stage.',
    )

    @api.depends(
        'task_id', 'task_id.kanban_state', 'task_id.project_id.block_picking',
        'task_id.project_id.active', 'task_id.project_id.stage_id.fold')
    def _compute_picking_blocked(self):
        for picking in self:
            task = picking.task_id
            project = task.project_id
            picking.picking_blocked = bool(task and (
                task.kanban_state == 'blocked' or (project and (
                    project.block_picking
                    or not project.active
                    or project.stage_id.fold))))
