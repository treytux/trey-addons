###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import socket
from datetime import timedelta

from odoo import api, fields, models


class PreventiveCronHistory(models.Model):
    _name = 'preventive.maintenance.cron.history'
    _description = 'Preventive maintenance cron execution history'
    _order = 'date_start desc, id desc'
    _rec_name = 'cron_id'

    cron_id = fields.Many2one(
        comodel_name='ir.cron',
        string='Scheduled Action',
        required=True,
        ondelete='cascade',
        index=True,
    )
    date_start = fields.Datetime(
        string='Started',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    date_end = fields.Datetime(
        string='Ended',
    )
    duration_sec = fields.Float(
        string='Duration (s)',
        digits=(12, 3),
        compute='_compute_duration_sec',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('running', 'Running'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ],
        required=True,
        default='running',
        index=True,
    )
    error_traceback = fields.Text(string='Error Traceback')
    server_name = fields.Char(
        string='Server',
        default=lambda self: socket.gethostname(),
        readonly=True,
    )

    _sql_constraints = [(
        'date_order',
        'CHECK (date_end IS NULL OR date_end >= date_start)',
        'End time must be on or after start time.',
    )]

    @api.depends('date_start', 'date_end')
    def _compute_duration_sec(self):
        for record in self:
            record.duration_sec = ((
                record.date_end - record.date_start).total_seconds()
                if record.date_start and record.date_end else 0.0)

    @api.model
    def cleanup(self, retention_days, batch_size):
        if retention_days is None or not isinstance(retention_days, int):
            raise ValueError('retention_days must be an integer')
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError('batch_size must be a positive integer')
        if retention_days <= 0:
            return 0
        cutoff = fields.Datetime.now() - timedelta(days=retention_days)
        rows = self.search([
            ('date_start', '<', cutoff),
        ], limit=batch_size, order='date_start asc')
        count = len(rows)
        rows.unlink()
        return count
