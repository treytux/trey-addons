###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountInvoiceAgentAssignment(TransactionCase):

    def setUp(self):
        super(TestAccountInvoiceAgentAssignment, self).setUp()
        self.commission_net_paid = self.env['sale.commission'].create({
            'name': '20% fixed commission (Net amount) - Payment Based',
            'fix_qty': 20.0,
            'invoice_state': 'paid',
            'amount_base_type': 'net_amount',
        })
        self.agent_01 = self.env['res.partner'].create({
            'name': 'Agent 01',
            'agent': True,
            'email': 'agent01@test.com',
            'commission': self.commission_net_paid.id,
        })
        self.agent_02 = self.env['res.partner'].create({
            'name': 'Agent 02',
            'agent': True,
            'email': 'agent02@test.com',
            'commission': self.commission_net_paid.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522',
            'agents': [(6, 0, [self.agent_01.id])],
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test Product',
            'standard_price': 5,
            'list_price': 50,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test Product',
            'standard_price': 10,
            'list_price': 100,
        })

    def test_invoice_assignment_agent(self):
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner.property_account_receivable_id = account_customer.id
        self.partner.property_account_payable_id = account_supplier.id
        journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': account_sale.id,
            'default_credit_account_id': account_sale.id,
        })
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.tax = self.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale')], limit=1)
        invoice = self.env['account.invoice'].create({
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_01.id,
                'name': self.product_01.name,
                'account_id': account_sale.id,
                'price_unit': 100,
                'quantity': 1})],
        })
        invoice.action_invoice_open()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.agents.agent.id, self.agent_01.id)
        wizard = self.env['account.invoice.agent.assignment'].with_context({
            'active_ids': invoice.ids,
            'active_id': invoice.id,
        }).create({
            'agents': [(6, 0, [self.agent_02.id])],
        })
        wizard.button_accept()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.agents.agent.id, self.agent_02.id)
