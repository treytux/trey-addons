###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import tools
from odoo.tests.common import TransactionCase


class TestIrModelLogRollback(TransactionCase):

    def setUp(self):
        super().setUp()
        self.log = self.env['ir.model.log']

    def test_rollback_preserves_log_after_db_rollback(self):
        log = self.log.create({
            'name': 'Rollback Persist Test',
            'description': 'Log before rollback',
            'res_model': 'res.partner',
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner to be rolled back',
        })
        log.info('Partner created')
        result_log = log.rollback(force=True)
        self.assertTrue(result_log.exists())
        self.assertIn('Log before rollback', result_log.description)
        self.assertIn('Partner created', result_log.description)
        partner_after = self.env['res.partner'].browse(partner.id)
        if not tools.config.get('test_enable'):
            self.assertFalse(partner_after.exists())
