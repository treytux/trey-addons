###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'ir.model.log'

    is_preventive_maintenance = fields.Boolean(
        string='Is maintenance',
        default=False,
        readonly=True,
    )
    type = fields.Selection(
        selection=[
            ('other', 'Other'),
            ('cron_history', 'Cron history'),
            ('records_integrity', 'Records integrity'),
            ('storage', 'Storage'),
            ('slow_query_history', 'Slow query history'),
        ],
        string='Type',
        default='other',
        readonly=True,
        index=True,
    )

    def remove_preventive_maintenance_logs(self):
        logs = self.sudo().search([
            ('is_preventive_maintenance', '=', True),
        ])
        logs.unlink()
