###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import SUPERUSER_ID
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner1',
        })
        self.force_number_group = self.env.ref(
            'sale_order_edit_number.group_sale_order_force_number')
        self.env.user.groups_id |= self.force_number_group

    def _create_sale(self, **vals):
        return self.env['sale.order'].create(dict(
            partner_id=self.partner.id, **vals))

    def test_create_without_force_number(self):
        sale = self._create_sale()
        self.assertTrue(sale.name)

    def test_create_with_force_number(self):
        sale = self._create_sale(force_number='SO-999')
        self.assertEqual(sale.name, 'SO-999')

    def test_create_with_name_and_force_number(self):
        sale = self._create_sale(name='SO-1002', force_number='SO-1000')
        self.assertEqual(sale.name, 'SO-1002')

    def test_create_duplicate_force_number(self):
        self._create_sale(force_number='SO-999')
        with self.assertRaises(UserError) as error:
            self._create_sale(force_number='SO-999')
        self.assertEqual(
            str(error.exception), 'Sale order number SO-999 already exists!')

    def test_write_force_number(self):
        sale = self._create_sale(force_number='SO-1000')
        sale.write({'force_number': 'SO-15000'})
        self.assertEqual(sale.name, 'SO-15000')

    def test_write_same_force_number(self):
        sale = self._create_sale(force_number='SO-2000')
        sale.write({'force_number': 'SO-2000'})
        self.assertEqual(sale.name, 'SO-2000')

    def test_write_duplicate_force_number(self):
        self._create_sale(force_number='SO-999')
        sale = self._create_sale(force_number='SO-1000')
        with self.assertRaises(UserError) as error:
            sale.write({'force_number': 'SO-999'})
        self.assertEqual(
            str(error.exception), 'Sale order number SO-999 already exists!')

    def test_write_force_number_multi_record(self):
        sales = self._create_sale() + self._create_sale()
        with self.assertRaises(UserError) as error:
            sales.write({'force_number': 'SO-3000'})
        self.assertEqual(
            str(error.exception),
            'You cannot force the number on several sale orders at once.')

    def test_copy_resets_force_number(self):
        sale = self._create_sale(force_number='SO-999')
        copy = sale.copy()
        self.assertTrue(copy.name)
        self.assertNotEqual(copy.name, sale.name)
        self.assertFalse(copy.force_number)

    def test_force_number_field_hidden_without_group(self):
        self.env.user.groups_id -= self.force_number_group
        user = self.env['res.users'].create({
            'name': 'Salesman',
            'login': 'salesman_force_number',
            'groups_id': [
                (6, 0, [self.env.ref('sales_team.group_sale_salesman').id])],
        })
        with self.assertRaises(AccessError):
            self.env['sale.order'].with_user(user).create({
                'partner_id': self.partner.id,
                'force_number': 'SO-4000',
            })

    def test_superuser_cannot_force_number_without_group(self):
        self.env.ref('base.user_root').groups_id -= self.force_number_group
        with self.assertRaises(AccessError) as error:
            self.env['sale.order'].with_user(SUPERUSER_ID).create({
                'partner_id': self.partner.id,
                'force_number': 'SO-5000',
            })
        self.assertEqual(
            str(error.exception),
            'You are not allowed to force the sale order number.')
