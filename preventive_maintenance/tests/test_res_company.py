###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPreventiveMaintenanceResCompany(TransactionCase):
    def setUp(self):
        super().setUp()
        self.History = self.env['preventive.maintenance.cron.history']
        self.Log = self.env['ir.model.log']
        action = self.env['ir.actions.server'].create({
            'name': 'Preventive res.company test action',
            'model_id': self.env.ref('base.model_ir_cron').id,
            'state': 'code',
            'code': 'pass',
        })
        self.cron = self.env['ir.cron'].create({
            'name': 'Preventive res.company test cron',
            'ir_actions_server_id': action.id,
            'interval_number': 1,
            'interval_type': 'days',
            'active': False,
        })
        self.History.search([]).unlink()

    def _history(self, start, state='success', duration=10.0):
        end = start + timedelta(seconds=duration)
        return self.History.create({
            'cron_id': self.cron.id,
            'date_start': start,
            'date_end': end,
            'state': state,
            'error_traceback': (
                'Traceback: test failure' if state == 'failed' else False),
        })

    def test_run_cron_history_filters_period_and_aggregates_results(self):
        now = fields.Datetime.now()
        old = self._history(now - timedelta(days=10), duration=4.0)
        recent_success = self._history(now - timedelta(hours=2), duration=3.0)
        recent_failure = self._history(
            now - timedelta(hours=1), state='failed', duration=5.0)
        report = self.env['res.company'].run_cron_history(7, 10)
        ids = {row['id'] for row in report['executions']}
        self.assertNotIn(old.id, ids)
        self.assertEqual(ids, {recent_success.id, recent_failure.id})
        self.assertEqual(report['summary']['executions_returned'], 2)
        self.assertEqual(report['summary']['failed_executions'], 1)
        cron_summary = report['summary']['by_cron'][self.cron.name]
        self.assertEqual(cron_summary['executions'], 2)
        self.assertEqual(cron_summary['failed'], 1)
        self.assertEqual(cron_summary['duration_sec'], 8.0)
        self.assertFalse(report['truncated'])

    def test_run_cron_history_marks_truncated_reports(self):
        now = fields.Datetime.now()
        self._history(now - timedelta(minutes=3))
        self._history(now - timedelta(minutes=2))
        self._history(now - timedelta(minutes=1))
        report = self.env['res.company'].run_cron_history(1, 2)
        self.assertEqual(report['summary']['executions_returned'], 2)
        self.assertTrue(report['truncated'])

    def test_run_cron_history_creates_preventive_log(self):
        self._history(fields.Datetime.now())
        report = self.env['res.company'].run_cron_history(1, 10)
        log = self.Log.browse(report['log_id'])
        self.assertTrue(log.exists())
        self.assertTrue(log.is_preventive_maintenance)
        self.assertEqual(log.res_model, 'preventive.maintenance.cron.history')

    def test_run_records_integrity_detects_duplicate_contacts(self):
        first = self.env['res.partner'].create({
            'name': 'Integrity Contact One',
            'email': 'duplicate.integrity@example.com',
        })
        second = self.env['res.partner'].create({
            'name': 'Integrity Contact Two',
            'email': 'duplicate.integrity@example.com',
        })
        reports = self.env['res.company'].run_records_integrity(
            companies=self.env.company, max_groups=50, max_ids_per_group=50,
            fuzzy_name_threshold=0.95)
        company_report = next(
            report for report in reports
            if report['scope']['type'] == 'company')
        email_findings = [
            finding for finding in company_report['checks']
            if finding['check'] == 'contact.email_duplicate']
        self.assertTrue(email_findings)
        self.assertTrue(
            {first.id, second.id}
            .issubset(set(email_findings[0]['record_ids'])))
        self.assertEqual(email_findings[0]['severity'], 'high')

    def test_run_records_integrity_allows_parent_phone_and_address_name(self):
        parent = self.env['res.partner'].create({
            'name': 'Preventive Parent Company',
            'is_company': True,
            'phone': '+34910000123',
        })
        child = self.env['res.partner'].create({
            'name': 'Preventive Child Contact',
            'parent_id': parent.id,
            'phone': '+34 910 000 123',
        })
        address = self.env['res.partner'].create({
            'name': False,
            'type': 'delivery',
        })
        other_parent = self.env['res.partner'].create({
            'name': 'Preventive Other Company',
            'is_company': True,
        })
        same_name_other_parent = self.env['res.partner'].create({
            'name': child.name,
            'parent_id': other_parent.id,
        })
        reports = self.env['res.company'].run_records_integrity(
            companies=self.env.company, max_groups=50, max_ids_per_group=50,
            fuzzy_name_threshold=0.95)
        company_report = next(
            report for report in reports
            if report['scope']['type'] == 'company')
        checks = company_report['checks']
        phone_findings = [
            finding for finding in checks
            if finding['check'] == 'contact.phone_duplicate']
        name_findings = [
            finding for finding in checks
            if finding['check'] == 'contact.name_duplicate']
        missing_name_findings = [
            finding for finding in checks
            if finding['check'] == 'contact.name_missing']
        self.assertFalse(any(
            child.id in finding['record_ids']
            and parent.id in finding['record_ids']
            for finding in phone_findings))
        self.assertFalse(any(
            same_name_other_parent.id in finding['record_ids']
            and child.id in finding['record_ids']
            for finding in name_findings))
        self.assertNotIn(
            address.id,
            [record_id for finding in missing_name_findings
             for record_id in finding['record_ids']])

    def test_storage_usage_detects_duplicate_attachment_metadata(self):
        partner = self.env['res.partner'].create({
            'name': 'Preventive Attachment Target',
        })
        first = self.env['ir.attachment'].create({
            'name': 'preventive-same-name.txt',
            'datas': base64.b64encode(b'first'),
            'res_model': 'res.partner',
            'res_id': partner.id,
        })
        second = self.env['ir.attachment'].create({
            'name': first.name,
            'datas': base64.b64encode(b'second'),
            'res_model': first.res_model,
            'res_id': first.res_id,
        })
        report = self.env['res.company'].run_storage_usage(
            companies=self.env.company, inactive_limit=1,
            large_attachment_limit=1024 * 1024, max_size_tables=5,
            max_growth_tables=5, growth_period=3)
        company_report = next(
            value for value in report if value['scope']['type'] == 'company')
        duplicate_ids = [
            attachment['id']
            for group in company_report['duplicate_attachments']
            for attachment in group['attachments']]
        self.assertIn(first.id, duplicate_ids)
        self.assertIn(second.id, duplicate_ids)

    def test_fuzzy_contact_check_uses_escaped_trigram_operator(self):
        self.env.cr.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
        if not self.env.cr.fetchone():
            self.skipTest('pg_trgm is not installed in the test database.')

        self.env['res.partner'].create({
            'name': 'Fuzzy Contact Regression Alpha',
        })
        self.env['res.partner'].create({
            'name': 'Fuzzy Contact Regression Alfa',
        })
        reports = self.env['res.company'].run_records_integrity(
            companies=self.env.company, max_groups=50, max_ids_per_group=50,
            fuzzy_name_threshold=0.7)
        for report in reports:
            failures = [
                finding for finding in report['checks']
                if (
                    finding['check'] == 'audit.check_failed'
                    and finding['audit_check'] == 'contacts')]
            self.assertFalse(failures)

    def test_integrity_skips_unavailable_role_checks(self):
        company_model = self.env['res.company']
        with patch.object(
            type(company_model), '_partner_role_conditions',
                return_value=[]):
            reports = company_model.run_records_integrity(
                companies=self.env.company, max_groups=10,
                max_ids_per_group=10, fuzzy_name_threshold=0.95)

        company_report = next(
            report for report in reports
            if report['scope']['type'] == 'company')
        skipped = [
            finding
            for finding in company_report['checks']
            if finding['check'] == 'contact.role_fields_unavailable']
        self.assertEqual(len(skipped), 1)

    def test_run_storage_usage_reports_inactive_and_large_attachment(self):
        inactive = self.env['res.partner'].create({
            'name': 'Inactive Preventive Test Contact',
            'active': False,
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'preventive-large-test.bin',
            'datas': base64.b64encode(b"x" * 2048),
            'res_model': 'res.partner',
            'res_id': inactive.id,
        })
        deleted_partner = self.env['res.partner'].create({
            'name': 'Deleted Preventive Test Contact',
        })
        deleted_partner_id = deleted_partner.id
        deleted_partner.unlink()
        broken_attachment = self.env['ir.attachment'].create({
            'name': 'preventive-broken-test.bin',
            'datas': base64.b64encode(b"broken"),
            'res_model': 'res.partner',
            'res_id': deleted_partner_id,
        })
        reports = self.env['res.company'].run_storage_usage(
            companies=self.env.company, inactive_limit=1,
            large_attachment_limit=1024, max_size_tables=5,
            max_growth_tables=5, growth_period=3)
        company_report = next(
            report for report in reports
            if report['scope']['type'] == 'company')
        inactive_models = {
            row['model']: row['inactive_count']
            for row in company_report['inactive_models']
        }
        large_attachments = {
            row['id'] for row in company_report['large_attachments']}
        broken_attachments = {
            row['id']
            for row in company_report['attachments_with_broken_reference']}
        self.assertGreaterEqual(inactive_models.get('res.partner', 0), 1)
        self.assertIn(attachment.id, large_attachments)
        self.assertIn(broken_attachment.id, broken_attachments)
        self.assertGreaterEqual(company_report['summary']['models'], 1)
        self.assertGreaterEqual(
            company_report['summary']['large_attachments'], 1)
