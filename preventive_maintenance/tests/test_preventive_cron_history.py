###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPreventiveCronHistory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.History = self.env['preventive.maintenance.cron.history']
        self.Log = self.env['ir.model.log']
        self.Cron = self.env['ir.cron']
        server_action = self.env['ir.actions.server'].create({
            'name': 'Preventive maintenance test action',
            'model_id': self.env.ref('base.model_ir_cron').id,
            'state': 'code',
            'code': 'pass',
        })
        self.cron = self.Cron.create({
            'name': 'Preventive maintenance test cron',
            'ir_actions_server_id': server_action.id,
            'interval_number': 1,
            'interval_type': 'days',
            'active': False,
        })
        self.History.search([]).unlink()

    def _history(self, **values):
        vals = {
            'cron_id': self.cron.id,
            'date_start': fields.Datetime.now() - timedelta(hours=1),
            'date_end': fields.Datetime.now(),
            'state': 'success',
        }
        vals.update(values)
        return self.History.create(vals)

    def test_duration_is_computed(self):
        history = self.History.create({
            'cron_id': self.cron.id,
            'date_start': '2026-01-01 10:00:00',
            'date_end': '2026-01-01 10:00:42',
            'state': 'success',
        })
        self.assertEqual(history.duration_sec, 42.0)

    def test_failed_history_keeps_traceback(self):
        history = self._history(
            state='failed',
            error_traceback='Traceback: preventive test failure')
        self.assertEqual(history.state, 'failed')
        self.assertIn('preventive test failure', history.error_traceback)

    def test_report_creates_marked_json_log(self):
        failed = self._history(
            state='failed',
            error_traceback='Traceback: scheduled action failed')
        successful = self._history(state='success')
        report = self.env['res.company'].run_cron_history(
            days=7, max_records=10)
        self.assertEqual(report['summary']['executions_returned'], 2)
        self.assertEqual(report['summary']['failed_executions'], 1)
        self.assertEqual(report['summary']['by_state']['failed'], 1)
        self.assertEqual(report['summary']['by_state']['success'], 1)
        self.assertEqual(
            {row['id'] for row in report['executions']},
            {failed.id, successful.id})
        log = self.Log.browse(report['log_id'])
        self.assertTrue(log.exists())
        self.assertTrue(log.is_preventive_maintenance)
        self.assertEqual(log.res_model, 'preventive.maintenance.cron.history')
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'ir.model.log'),
            ('res_id', '=', log.id),
            ('name', '=', 'cron_history_analysis.json'),
        ], limit=1)
        self.assertTrue(attachment)
        payload = json.loads(base64.b64decode(attachment.datas).decode())
        self.assertEqual(payload['summary']['failed_executions'], 1)

    def test_analysis_alias_creates_report(self):
        self._history()
        report = self.env['res.company'].run_cron_analysis(
            days=1, max_records=10)
        self.assertTrue(report['log_id'])

    def test_report_accepts_positional_arguments_from_automated_actions(self):
        self._history()
        report = self.env['res.company'].run_cron_history(1, 10)
        self.assertTrue(report['log_id'])

    def test_report_rejects_invalid_parameters(self):
        Company = self.env['res.company']
        with self.assertRaises(ValueError):
            Company.run_cron_history(days=0, max_records=10)
        with self.assertRaises(ValueError):
            Company.run_cron_history(days=7, max_records=0)

    def test_cleanup_removes_old_rows_and_keeps_recent_rows(self):
        old = self._history(
            date_start=fields.Datetime.now() - timedelta(days=31),
            date_end=fields.Datetime.now() - timedelta(days=31))
        recent = self._history(
            date_start=fields.Datetime.now() - timedelta(days=5),
            date_end=fields.Datetime.now() - timedelta(days=5))
        removed = self.History.cleanup(retention_days=30, batch_size=5000)
        self.assertEqual(removed, 1)
        self.assertFalse(old.exists())
        self.assertTrue(recent.exists())

    def test_cleanup_disabled_for_non_positive_retention(self):
        old = self._history(
            date_start=fields.Datetime.now() - timedelta(days=31),
            date_end=fields.Datetime.now() - timedelta(days=31))
        self.assertEqual(self.History.cleanup(
            retention_days=0, batch_size=5000), 0)
        self.assertTrue(old.exists())

    def test_preventive_log_removal_does_not_remove_other_logs(self):
        preventive = self.Log.create({
            'name': 'Preventive test log',
            'is_preventive_maintenance': True,
        })
        other = self.Log.create({'name': 'Other test log'})
        self.Log.remove_preventive_maintenance_logs()
        self.assertFalse(preventive.exists())
        self.assertTrue(other.exists())

    def test_existing_company_reports_are_marked_preventive(self):
        self.env['res.company']._log_maintenance_result(
            self.env.company, {'test': True}
        )
        log = self.Log.search([
            ('name', '=', 'Maintenance report for %s' % self.env.company.name),
            ('res_model', '=', 'res.company'),
            ('is_preventive_maintenance', '=', True),
        ], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertTrue(log.is_preventive_maintenance)
