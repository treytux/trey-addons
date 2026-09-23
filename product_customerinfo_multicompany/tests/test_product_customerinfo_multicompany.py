###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo.exceptions import AccessError
from odoo.tests import common


class TestProductCustomerinfoMulticompany(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company_a = self.env['res.company'].create({
            'name': 'Customerinfo Company A',
        })
        self.company_b = self.env['res.company'].create({
            'name': 'Customerinfo Company B',
        })
        self.user_a = self.env['res.users'].create({
            'name': 'Customerinfo User A',
            'login': 'customerinfo_user_a_test',
            'password': 'test',
            'company_id': self.company_a.id,
            'company_ids': [(6, 0, [self.company_a.id])],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.product = self.env.ref('product.product_product_4')
        partner = self.env['res.partner'].create({
            'name': 'Customerinfo Test Customer',
        })
        self.customerinfo_model = self.env['product.customerinfo']
        self.customerinfo_a = self.customerinfo_model.create({
            'partner_id': partner.id,
            'product_id': self.product.id,
            'price': 10.0,
            'company_id': self.company_a.id,
        })
        self.customerinfo_b = self.customerinfo_model.create({
            'partner_id': partner.id,
            'product_id': self.product.id,
            'price': 20.0,
            'company_id': self.company_b.id,
        })
        self.customerinfo_global = self.customerinfo_model.create({
            'partner_id': partner.id,
            'product_id': self.product.id,
            'price': 30.0,
            'company_id': False,
        })

    def test_user_sees_own_company_and_global_customerinfos(self):
        customerinfos = self.customerinfo_model.with_user(
            self.user_a).search([])
        self.assertEqual(
            set(customerinfos.ids), {
                self.customerinfo_a.id,
                self.customerinfo_global.id,
            })

    def test_user_cannot_read_other_company_customerinfo(self):
        with self.assertRaises(AccessError):
            self.customerinfo_model.with_user(self.user_a).browse(
                self.customerinfo_b.id).read(['price'])
