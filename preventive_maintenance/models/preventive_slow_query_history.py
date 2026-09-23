###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import api, fields, models


class PreventiveSlowQueryHistory(models.Model):
    _name = 'preventive.maintenance.slow.query.history'
    _description = 'Preventive maintenance slow query history'
    _order = 'date_last desc, id desc'

    query_id = fields.Char(
        string='Query ID',
        required=True,
        readonly=True,
        index=True,
    )
    bucket_start = fields.Datetime(
        string='Bucket start',
        required=True,
        readonly=True,
        index=True,
    )
    date_first = fields.Datetime(
        string='First seen',
        required=True,
        readonly=True,
        index=True,
    )
    date_last = fields.Datetime(
        string='Last seen',
        required=True,
        readonly=True,
        index=True,
    )
    occurrence_count = fields.Integer(
        string='Occurrences',
        required=True,
        readonly=True,
    )
    total_duration_ms = fields.Float(
        string='Total duration (ms)',
        readonly=True,
    )
    min_duration_ms = fields.Float(
        string='Minimum duration (ms)',
        readonly=True,
    )
    max_duration_ms = fields.Float(
        string='Maximum duration (ms)',
        readonly=True,
        index=True,
    )
    is_overflow = fields.Boolean(
        string='Dropped event counter',
        readonly=True,
        index=True,
    )
    server_name = fields.Char(
        string='Server',
        required=True,
        readonly=True,
        index=True,
    )

    _sql_constraints = [(
        'slow_query_bucket',
        'UNIQUE(query_id, bucket_start, server_name)',
        'A slow-query bucket can only be stored once per server.',
    )]

    @api.model
    def cleanup(self, retention_days, batch_size):
        if not isinstance(retention_days, int):
            raise ValueError('retention_days must be an integer')
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError('batch_size must be a positive integer')
        if retention_days <= 0:
            return 0
        cutoff = fields.Datetime.now() - timedelta(days=retention_days)
        rows = self.search([
            ('date_last', '<', cutoff),
        ], limit=batch_size, order='date_last asc, id asc')
        count = len(rows)
        rows.unlink()
        return count
