###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSecurity(TransactionCase):

    def test_group_partner_customer_created(self):
        user = self.env.ref('base.user_demo')
        group = self.env.ref('security.group_partner_customer_created')
        user.groups_id = [(4, group.id)]
        partner_obj = self.env['res.partner'].sudo(user)
        partners = partner_obj.search([])
        self.assertEquals(len(partners), 1)
        user.groups_id = [(3, group.id)]
        self.env.ref('base.res_partner_3').sudo(user).copy({
            'name': 'Partner for test group_partner_customer_created'})
        user.groups_id = [(4, group.id)]
        partners = partner_obj.search([])
        self.assertEquals(len(partners), 2)
        user.groups_id = [(3, group.id)]

    def test_group_partner_customer_salesman(self):
        user = self.env.ref('base.user_demo')
        group = self.env.ref('security.group_partner_customer_salesman')
        user.groups_id = [(4, group.id)]
        partner_obj = self.env['res.partner'].sudo(user)
        partners = partner_obj.search([])
        self.assertEquals(len(partners), 1)
        user.groups_id = [(3, group.id)]
        self.env.ref('base.res_partner_3').sudo(user).copy({
            'user_id': user.id,
            'name': 'Partner for test group_partner_customer_salesman'})
        user.groups_id = [(4, group.id)]
        partners = partner_obj.search([])
        self.assertEquals(len(partners), 2)
        user.groups_id = [(3, group.id)]

    def test_group_product_readonly(self):
        user = self.env['res.users'].create({
            'name': 'Test',
            'login': 'test',
            'email': 'test@test.com'})
        user.groups_id = [(6, 0, [self.env.ref('base.group_user').id])]
        write_group = self.env.ref('security.group_product_update')
        product_tmpl = self.env.ref(
            'product.product_product_3_product_template')
        product = self.env['product.product'].sudo(user).browse(
            product_tmpl.product_variant_id.id)
        self.assertRaises(Exception, product.write, {'name': 'Test!!!'})
        user.groups_id = [(4, write_group.id)]
        product.write({'name': 'Test!!!'})
        self.assertRaises(Exception, product.create, {'name': 'Test!!!'})
        create_group = self.env.ref('security.group_product_create')
        user.groups_id = [(4, create_group.id)]
        product = self.env['product.product'].sudo(user).browse(
            product_tmpl.product_variant_id.id)
        product.create({'name': 'Test!!!'})
