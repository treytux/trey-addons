###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    financial = fields.Boolean(
        string='Only Financial',
        help='Check this box if this budget use only financial data.',
    )
    include_subtasks = fields.Boolean(
        default=True,
        help='Check this box if must be computed tasks and subtasks.',
    )
