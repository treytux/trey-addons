###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

from odoo import tools
from odoo.addons.woocommerce_connector.tests import test_common as common
from odoo.exceptions import UserError


class TestWooLog(common.TestCommon):

    def test_log_created_on_sync_import(self):
        log_obj = self.env['ir.model.log']
        initial_logs = log_obj.search_count([
            ('website_id', '=', self.website.id),
        ])
        self.assertEqual(initial_logs, 0)

    def test_log_has_website_field(self):
        log = self.env['ir.model.log'].create({
            'name': 'Test Log',
            'website_id': self.website.id,
        })
        self.assertEqual(log.website_id, self.website)

    def test_log_info_method(self):
        log = self.env['ir.model.log'].create({
            'name': 'Info Test',
            'description': '',
        })
        log.info('Test info message')
        self.assertIn('Test info message', log.description)

    def test_log_warn_method(self):
        log = self.env['ir.model.log'].create({
            'name': 'Warn Test',
            'description': '',
        })
        log.warn('Test warning message')
        self.assertIn('Test warning message', log.description)

    def test_log_error_method(self):
        log = self.env['ir.model.log'].create({
            'name': 'Error Test',
            'description': '',
        })
        log.error('Test error message')
        self.assertIn('Test error message', log.description)

    def test_log_exception_method(self):
        log = self.env['ir.model.log'].create({
            'name': 'Exception Test',
            'description': '',
        })
        try:
            raise ValueError('Simulated error')
        except ValueError as ex:
            log.exception('Error during operation', ex)
        self.assertIn('Error during operation', log.description)
        self.assertIn('Simulated error', log.description)

    def test_log_add_id(self):
        log = self.env['ir.model.log'].create({
            'name': 'Add ID Test',
            'res_ids': '[]',
        })
        log.add_id(self.product.id)
        self.assertEqual(log.res_ids_count, 1)
        log.add_id(self.categ.id)
        self.assertEqual(log.res_ids_count, 2)

    def test_log_attach(self):
        log = self.env['ir.model.log'].create({
            'name': 'Attach Test',
        })
        content = '{"product": "test"}'
        log.attach('test.json', content)
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'ir.model.log'),
            ('res_id', '=', log.id),
        ])
        self.assertTrue(attachment)

    def test_log_get_or_create_existing(self):
        log_obj = self.env['ir.model.log']
        log1 = log_obj.create({
            'name': 'Import products',
            'website_id': self.website.id,
        })
        log2 = log_obj.get_or_create_log({
            'name': 'Import products',
            'website_id': self.website.id,
        })
        self.assertEqual(log1.id, log2.id)

    def test_log_get_or_create_new(self):
        log_obj = self.env['ir.model.log']
        log = log_obj.get_or_create_log({
            'name': 'New import operation',
            'website_id': self.website.id,
        })
        self.assertTrue(log.exists())

    def test_log_finish(self):
        log = self.env['ir.model.log'].create({
            'name': 'Finish Test',
            'description': '',
        })
        self.assertFalse(log.date_finish)
        log.finish('Operation completed')
        self.assertTrue(log.date_finish)
        self.assertIn('Operation completed', log.description)


class TestWooLogRollback(common.TestCommon):

    def test_rollback_skipped_in_test_mode(self):
        log = self.env['ir.model.log'].create({
            'name': 'Rollback Test',
            'description': 'Initial description',
            'website_id': self.website.id,
        })
        log.description = 'Modified description'
        result = log.rollback()
        self.assertEqual(result, log)
        self.assertEqual(log.description, 'Modified description')

    def test_rollback_forced_preserves_log(self):
        log = self.env['ir.model.log'].create({
            'name': 'Forced Rollback Test',
            'description': 'Initial log state',
            'website_id': self.website.id,
        })
        partner = self.env['res.partner'].create({
            'name': '[OdooWooConn] Test Partner Rollback',
        })
        partner_id = partner.id
        log.info('Partner created for test')
        result_log = log.rollback(force=True)
        self.assertTrue(result_log.exists())
        self.assertIn('Initial log state', result_log.description)
        self.assertIn('Partner created for test', result_log.description)
        partner_after = self.env['res.partner'].browse(partner_id)
        # In test mode the DB rollback is skipped to preserve savepoints
        if not tools.config.get('test_enable'):
            self.assertFalse(partner_after.exists())


class TestWooSyncImportLog(common.TestCommon):

    def test_sync_import_creates_log(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        log_obj = self.env['ir.model.log']
        initial_count = log_obj.search_count([
            ('name', 'like', 'Import%'),
            ('website_id', '=', self.website.id),
        ])
        self.assertEqual(initial_count, 0)

    @patch('odoo.addons.woocommerce_connector.models.website_woo_mixin.'
           'WebsiteWooMixin.woo_rpc_call')
    def test_sync_import_with_error_logs_exception(self, mock_rpc):
        mock_rpc.return_value = [{
            'id': 1,
            'name': 'Test Product',
            'sku': 'TEST-001',
        }]
        log_obj = self.env['ir.model.log']
        log = log_obj.create({
            'name': 'Import test',
            'website_id': self.website.id,
            'description': '',
        })
        log.info('Starting import')
        try:
            raise UserError('Simulated import error')
        except UserError as ex:
            log.exception('Import failed', ex)
        self.assertIn('Import failed', log.description)
        self.assertIn('Simulated import error', log.description)


class TestWooLogIntegration(common.TestCommon):

    def test_log_workflow_complete(self):
        log = self.env['ir.model.log'].create({
            'name': 'Complete Workflow Test',
            'website_id': self.website.id,
            'res_model': 'product.product',
            'description': '',
        })
        log.info('Step 1: Starting operation')
        log.add_id(self.product.id)
        log.info('Step 2: Product processed')
        log.warn('Step 3: Minor warning')
        log.finish('Operation completed successfully')
        self.assertIn('Step 1', log.description)
        self.assertIn('Step 2', log.description)
        self.assertIn('Step 3', log.description)
        self.assertIn('completed successfully', log.description)
        self.assertEqual(log.res_ids_count, 1)
        self.assertTrue(log.date_finish)
        self.assertTrue(log.elapsed)

    def test_log_workflow_with_error(self):
        log = self.env['ir.model.log'].create({
            'name': 'Error Workflow Test',
            'website_id': self.website.id,
            'res_model': 'product.product',
            'description': '',
        })
        log.info('Step 1: Starting operation')
        try:
            raise ValueError('Unexpected error during processing')
        except ValueError as ex:
            log.exception('Operation failed at step 2', ex)
        log.finish('Operation finished with errors')
        self.assertIn('Step 1', log.description)
        self.assertIn('Operation failed', log.description)
        self.assertIn('Unexpected error', log.description)
        self.assertIn('finished with errors', log.description)
