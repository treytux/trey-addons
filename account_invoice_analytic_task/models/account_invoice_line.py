###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )
