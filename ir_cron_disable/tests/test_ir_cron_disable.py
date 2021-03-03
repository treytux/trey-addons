###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestIrCronDisable(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.cron = self.env['ir.cron'].create({
            'name': 'Cron Tester',
            'model_id': self.env.ref('base.model_ir_autovacuum').id,
            'active': True,
        })
        self.cron_2 = self.env['ir.cron'].create({
            'name': 'Cron Tester 2',
            'model_id': self.env.ref('base.model_ir_autovacuum').id,
            'active': True,
        })

    def test_one_true_ir_cron_disable(self):
        self.assertTrue(self.cron.active)
        wizard = self.env['ir.cron.disable'].with_context({
            'active_ids': self.cron.ids,
            'active_id': self.cron.id,
        }).create({})
        wizard.accept_action()
        self.assertFalse(self.cron.active)

    def test_one_false_ir_cron_disable(self):
        self.cron.active = False
        wizard = self.env['ir.cron.disable'].with_context({
            'active_ids': self.cron.ids,
            'active_id': self.cron.id,
        }).create({})
        wizard.accept_action()
        self.assertFalse(self.cron.active)

    def test_several_ir_cron_disable(self):
        self.assertTrue(self.cron.active)
        self.assertTrue(self.cron_2.active)
        wizard = self.env['ir.cron.disable'].with_context({
            'active_ids': [
                self.cron.id,
                self.cron_2.id,
            ],
            'active_id': self.cron.id,
        }).create({})
        wizard.accept_action()
        self.assertFalse(self.cron.active)
        self.assertFalse(self.cron_2.active)
