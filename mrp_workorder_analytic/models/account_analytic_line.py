###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    productivity_id = fields.Many2one(
        comodel_name='mrp.workcenter.productivity',
        string='Work Order',
        readonly=True,
        copy=False,
    )
    workorder_id = fields.Many2one(
        related='productivity_id.workorder_id',
        string='Work Order',
        readonly=True,
        store=True,
    )
    production_id = fields.Many2one(
        related='workorder_id.production_id',
        string='Production Order',
        readonly=True,
        store=True,
    )
