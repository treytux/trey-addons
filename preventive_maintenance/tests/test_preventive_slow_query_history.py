###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json
from datetime import timedelta

from odoo import fields
from odoo.addons.preventive_maintenance import slow_query_logger
from odoo.tests.common import TransactionCase


class TestPreventiveSlowQueryHistory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.History = self.env['preventive.maintenance.slow.query.history']
        self.Log = self.env['ir.model.log']
        self.History.search([]).unlink()

    def _history(self, query_id='a' * 64, **values):
        now = fields.Datetime.now()
        vals = {
            'query_id': query_id,
            'bucket_start': now.replace(minute=0, second=0, microsecond=0),
            'date_first': now - timedelta(minutes=2),
            'date_last': now,
            'occurrence_count': 2,
            'total_duration_ms': 12000.0,
            'min_duration_ms': 5000.0,
            'max_duration_ms': 7000.0,
            'server_name': 'test-server',
        }
        vals.update(values)
        return self.History.create(vals)

    def test_report_aggregates_query_ids_without_sql_text(self):
        first = self._history()
        second = self._history(
            query_id='b' * 64,
            bucket_start=fields.Datetime.now() - timedelta(hours=1),
            total_duration_ms=15000.0, occurrence_count=3)
        overflow = self._history(
            query_id='__overflow__', is_overflow=True, occurrence_count=4,
            total_duration_ms=0.0, min_duration_ms=0.0, max_duration_ms=0.0,
            bucket_start=fields.Datetime.now() - timedelta(hours=2))
        report = self.env['res.company'].run_slow_query_history(1, 10)
        self.assertEqual(report['summary']['buckets_returned'], 2)
        self.assertEqual(report['summary']['query_ids_returned'], 2)
        self.assertEqual(report['summary']['dropped_events_returned'], 4)
        self.assertEqual(
            {row['id'] for row in report['buckets']}, {first.id, second.id})
        self.assertTrue(report['query_text_stored'] is False)
        log = self.Log.browse(report['log_id'])
        self.assertEqual(log.type, 'slow_query_history')
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'ir.model.log'),
            ('res_id', '=', log.id),
            ('name', '=', 'slow_query_history.json'),
        ], limit=1)
        payload = json.loads(base64.b64decode(attachment.datas).decode())
        self.assertNotIn('\'query\':', json.dumps(payload))
        self.assertTrue(overflow.exists())

    def test_cleanup_uses_bounded_batches(self):
        self._history(date_last=fields.Datetime.now() - timedelta(days=31))
        self._history(
            query_id='b' * 64,
            bucket_start=fields.Datetime.now() - timedelta(hours=1),
            date_last=fields.Datetime.now() - timedelta(days=32))
        removed = self.env['res.company'].cleanup_slow_query_history(30, 1)
        self.assertEqual(removed, 1)
        self.assertEqual(self.History.search_count([]), 1)

    def test_runtime_buffer_keeps_only_a_hash_of_the_query(self):
        buffer = slow_query_logger.SlowQueryBuffer()
        query = 'SELECT confidential_value FROM test_table WHERE id = %s'
        buffer.record('test_database', query, 5001.0)
        key = next(iter(buffer._buckets))
        self.assertEqual(len(key[1]), 64)
        self.assertNotIn('SELECT', key[1])
        self.assertNotIn('confidential', key[1])
