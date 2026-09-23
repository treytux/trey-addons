###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestPartnercommercialVisibility(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.group_show_all_partners = self.env.ref(
            'partner_commercial_visibility.group_all_partners')
        self.group_show_all_partners.users += self.env.user
        self.partner_model = self.env['res.partner']
        self.sale_order_model = self.env['sale.order']
        self.partner_01_commercial = self.partner_model.create({
            'name': 'Partner commercial 01',
            'company_id': False,
        })
        self.child_partner01 = self.partner_model.create({
            'name': 'Child Partner 01',
            'parent_id': self.partner_01_commercial.id,
            'company_id': False,
        })
        self.partner_02_commercial = self.env.ref('base.res_partner_2')
        self.partner_03_commercial = self.env.ref('base.res_partner_3')

        self.partner_04 = self.partner_model.create({
            'name': 'Partner commercial 04',
            'company_id': False,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'default_code': '01-PROD',
            'list_price': 100,
        })
        self.partners_commercial = [
            self.partner_01_commercial,
            self.partner_02_commercial,
            self.partner_03_commercial,
        ]
        self.group_sales_team = self.env.ref('sales_team.group_sale_salesman')
        self.group_sales_team_all_leads = self.env.ref(
            'sales_team.group_sale_salesman_all_leads')
        self.demo_user = self.env.ref('base.user_demo')
        self.group_sales_team_all_leads.users -= self.demo_user
        self.group_sales_team.users += self.demo_user
        self.user_01 = self.env['res.users'].create({
            'name': 'Internal User 01',
            'login': 'internal.user01@test.odoo.com',
            'email': 'internal.user01@test.odoo.com',
            'partner_id': self.partner_04.id,
            'groups_id': [
                (4, self.env.ref('base.group_user').id)],
        })
        for partner in self.partners_commercial:
            partner.user_id = self.demo_user

    def create_sale(self, partner, user):
        return self.sale_order_model.with_user(user).create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                }),
            ],
        })

    def test_user_without_group_can_see_only_his_partners_and_addresses(self):
        self.group_show_all_partners.users += self.demo_user
        partners = self.partner_model.with_user(self.demo_user).search([])
        self.assertEqual(len(partners), 39)
        self.group_show_all_partners.users -= self.demo_user
        partners = self.partner_model.with_user(self.demo_user).search([])
        partners_with_commercial = partners.filtered(
            lambda p: p.user_id == self.demo_user)
        self.assertEqual(len(partners), 12)
        self.assertEqual(len(partners_with_commercial), 3)
        self.assertIn(self.demo_user.partner_id, partners)
        self.assertIn(self.partner_01_commercial, partners)
        self.assertIn(self.partner_02_commercial, partners)
        self.assertIn(self.partner_03_commercial, partners)

    def test_02_contacts_commercial_with_other_followers(self):
        self.partner_01_commercial.message_subscribe([self.partner_04.id])
        partners = self.partner_model.with_user(self.demo_user).search([])
        self.assertFalse(self.partner_04 in partners)
        self.assertIn(self.partner_04,
                      self.partner_01_commercial.message_follower_ids.partner_id)
        have_not_access = (
            self.partner_04 in partners[1].message_follower_ids.partner_id)
        self.assertFalse(have_not_access)
        self.assertEqual(len(partners), 12)

    def test_access_to_partners_im_commercial_and_his_addresses(self):
        partners = self.partner_model.with_user(self.demo_user).search([])
        for partner in partners:
            if not self.demo_user.partner_id == partner:
                if not partner.parent_id:
                    self.assertEqual(partner.user_id, self.demo_user)
                else:
                    self.assertEqual(
                        partner.commercial_partner_id.user_id,
                        self.demo_user)

    def test_04_create_and_access_to_sale_order(self):
        partners = self.partner_model.with_user(self.demo_user).search([])
        sale_order = self.create_sale(self.partner_01_commercial, self.demo_user)
        All_sale_Orders = self.sale_order_model.with_user(self.demo_user).search([])
        self.assertIn(sale_order.partner_id, partners)
        for order in All_sale_Orders:
            self.assertIn(order.partner_id, partners)
            self.assertEqual(order.user_id, self.demo_user)

    def test_05_demo_create_contact(self):
        partners = self.partner_model.with_user(self.demo_user).search([])
        self.assertEqual(len(partners), 12)
        contact = self.env['res.partner'].with_user(self.demo_user).create({
            'name': 'contact created by demo',
            'email': 'contactbydemo@test.odoo.com',
        })
        partners = self.partner_model.with_user(self.demo_user).search([])
        self.assertEqual(contact.user_id, self.demo_user)
        self.assertEqual(len(partners), 13)
        partners_with_commercial = partners.filtered(
            lambda p: p.user_id == self.demo_user)
        self.assertEqual(len(partners_with_commercial), 4)
