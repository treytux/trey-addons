###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    purchase_count = fields.Integer(
        string='Purchase count',
        related='project_id.purchase_count',
    )

    def button_open_purchase_order(self):
        self.ensure_one()
        action = self.project_id.button_open_purchase_order()
        action['context'] = {
            'default_analytic_distribution': {
                f'{self.project_id.analytic_account_id.id}': 100,
            },
        }
        return action
