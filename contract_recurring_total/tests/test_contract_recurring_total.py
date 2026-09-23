from odoo.tests.common import TransactionCase


class TestContractRecurringTotal(TransactionCase):
    def setUp(self):
        super(TestContractRecurringTotal, self).setUp()
        self.partner = self.env.ref('base.res_partner_12')
        self.contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })

    def create_new_contract_line(self):
        self.contract_line = self.env['contract.line'].create({
            'name': 'Test line',
            'contract_id': self.contract.id,
            'quantity': 1,
            'price_unit': 100,
            'recurring_rule_type': 'quarterly',
        })

    def unlink_contract_line(self):
        self.contract_line.cancel()
        self.assertEqual(self.contract_line.state, 'canceled')
        self.contract_line._compute_price_subtotal()

    def test_recurring_total(self):
        self.create_new_contract_line()
        self.assertEqual(self.contract.recurring_total, 400)
        self.create_new_contract_line()
        self.assertEqual(self.contract.recurring_total, 800)
        self.unlink_contract_line()
        self.assertEqual(self.contract.recurring_total, 400)
