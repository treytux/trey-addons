###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestVendingMachine(TransactionCase):
    def setUp(self):
        super(TestVendingMachine, self).setUp()
        self.company = self.env.ref('base.main_company')
        self.location_parent = self.env['stock.location'].create({
            'name': 'Test Location parent',
            'usage': 'view',
            'company_id': self.company.id,
            'active': True,
        })
        self.warehouse = self.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TESTWH',
            'company_id': self.company.id,
            'deposit_parent_id': self.location_parent.id,
            'active': True,
        })
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
            'company_id': self.company.id,
            'location_id': self.location_parent.id,
            'active': True,
        })
        self.company_partner_id = self.env['res.partner'].create({
            'name': 'Test Company',
            'company_type': 'company',
            'is_company': True,
        })
        self.individual_partner_id = self.env['res.partner'].create({
            'name': 'Test Partner',
            'parent_id': self.company_partner_id.id,
            'type': 'delivery',
            'company_type': 'person',
            'company_id': self.company.id,
        })
        self.vending_machine = self.env['vending.machine'].create({
            'code': 'fakeCode',
            'signature_key': 'FakeApiKey',
            'company_id': 'FakecompanyId',
            'partner_id': self.individual_partner_id.id,
            'location_id': self.location.id,
            'warehouse_id': self.warehouse.id,
        })

    def test_get_stock_stock_from_api_with_wrong_keys(self):
        with self.assertRaises(UserError) as e:
            self.vending_machine.action_view_stock_from_api()
        self.assertEqual(
            str(e.exception.name),
            'Error when synchronizing stock from API. Check the machine'
            ' configuration or the API connection.')

    def test_action_replenish_opens_confirmation_wizard(self):
        action = self.vending_machine.action_replenish()
        self.assertEqual(
            action['res_model'], 'vending.machine.replenish.confirm')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(
            action['context']['default_vending_machine_id'],
            self.vending_machine.id)

    def test_action_move_to_deposit_with_wrong_keys(self):
        date_from = datetime.date(2023, 7, 1)
        date_to = datetime.date(2023, 7, 31)
        with self.assertRaises(UserError):
            self.vending_machine.action_move_to_deposit(
                date_from=date_from,
                date_to=date_to)
