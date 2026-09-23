###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestIrModelLog(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.log = self.env['ir.model.log']
        self.user_internal = self.env['res.users'].create({
            'name': 'Internal User Test',
            'login': 'internal.user',
            'email': 'internal.user@test.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def test_create_log_entry(self):
        log = self.log.create({
            'name': 'Test Operation',
            'res_model': 'res.partner',
            'res_ids': str([self.partner.id]),
        })
        self.assertEqual(log.name, 'Test Operation')
        self.assertEqual(log.res_model, 'res.partner')
        self.assertEqual(log.res_ids, str([self.partner.id]))
        self.assertEqual(log.res_ids_count, 1)

    def test_compute_res_ids(self):
        log = self.log.create({
            'name': 'Test compute',
            'res_model': 'res.partner',
            'res_ids': [1, 2, 3],
        })
        self.assertEqual(log.res_ids_count, 3)

    def test_add_id(self):
        log = self.log.create({
            'name': 'Add ID Test',
            'res_ids': '[]',
        })
        log.add_id(self.partner.id)
        self.assertEqual(log.res_ids, str([self.partner.id]))
        self.assertEqual(log.res_ids_count, 1)

    def test_action_view_records(self):
        log = self.log.create({
            'name': 'View Test',
            'res_model': 'res.partner',
            'res_ids': str([self.partner.id]),
        })
        action = log.action_view_records()
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertIn(('id', 'in', [self.partner.id]), action['domain'])

    def test_info_warn_error(self):
        log = self.log.create({
            'name': 'Log Message Test',
            'description': '',
        })
        log.info('Info message')
        self.assertIn('Info message', log.description)
        log.warn('Warning message')
        self.assertIn('Warning message', log.description)
        log.error('Error message')
        self.assertIn('Error message', log.description)

    def test_finish(self):
        log = self.log.create({
            'name': 'Finish Test',
            'date_start': datetime.now() - timedelta(minutes=5),
            'description': '',
        })
        log.finish('Finished successfully')
        self.assertIn('Finished successfully', log.description)

    def test_attach(self):
        log = self.log.create({'name': 'Attachment Test'})
        content = '{"status": "ok"}'
        log.attach('log.json', content)
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'ir.model.log'),
            ('res_id', '=', log.id),
            ('name', '=', 'log.json'),
        ])
        self.assertTrue(attachment)
        decoded_content = base64.b64decode(attachment.datas).decode()
        self.assertEqual(decoded_content, content)

    def test_internal_user_permissions(self):
        log = self.log.with_user(self.user_internal).create({
            'name': 'Log creation',
            'res_model': 'res.partner',
            'res_ids': str([self.partner.id]),
        })
        log_name = self.log.with_user(self.user_internal).browse(log.id).name
        self.assertEqual(log_name, 'Log creation')

    def test_get_or_create_log_existing(self):
        log = self.log.create({
            'name': 'Existing Log',
            'res_model': 'res.partner',
        })
        log2 = self.log.get_or_create_log({
            'name': 'Existing Log',
            'res_model': 'res.partner',
        })
        self.assertEqual(log.id, log2.id)

    def test_get_or_create_log_new(self):
        log = self.log.get_or_create_log({
            'name': 'New Log',
            'res_model': 'res.partner',
        })
        self.assertTrue(log.exists())
        self.assertEqual(log.name, 'New Log')

    def test_exception_method(self):
        log = self.log.create({
            'name': 'Exception Test',
            'description': '',
        })
        try:
            raise ValueError('Test error')
        except ValueError as ex:
            log.exception('Error occurred', ex)
        self.assertIn('Error occurred', log.description)
        self.assertIn('ValueError', log.description)

    def test_rollback_without_force_in_test_mode(self):
        log = self.log.create({
            'name': 'Rollback Test',
            'description': 'Initial',
        })
        log.description = 'Modified'
        result = log.rollback()
        self.assertEqual(result, log)
        self.assertEqual(log.description, 'Modified')
