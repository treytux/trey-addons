###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductCreateOrderpointAuto(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user_company = self.env.company
        self.assertTrue(self.user_company)
        self.warehouse = self.env['stock.warehouse'].search([]).filtered(
            lambda wh: wh.company_id.id == self.user_company.id)
        self.assertEqual(len(self.warehouse), 1)
        self.user_company.warehouse_auto_orderpoint_ids = [
            (6, 0, self.warehouse.ids)]
        self.assertEqual(
            len(self.user_company.warehouse_auto_orderpoint_ids), 1)
        self.attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr.id,
                'name': value,
            })

    def create_warehouse(self, key, company):
        return self.env['stock.warehouse'].create({
            'name': 'Warehouse %s' % key,
            'code': 'WH%s' % key,
            'company_id': company.id,
        })

    def create_new_company(self):
        return self.env['res.company'].create({
            'name': 'New test company',
        })

    def create_new_user(self, company):
        new_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [company.id])],
            'company_id': company.id,
            'groups_id': [(6, 0, [
                self.env.ref('stock.group_stock_manager').id,
                self.env.ref('stock.group_stock_multi_warehouses').id,
            ])],
        })
        new_user.partner_id.email = new_user.login
        return new_user

    def test_create_type_service(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertFalse(product.orderpoint_ids)

    def test_create_type_product_one_warehouse(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEqual(len(product.orderpoint_ids), 1)
        self.assertEqual(product.orderpoint_ids.warehouse_id, self.warehouse)
        self.assertEqual(
            product.orderpoint_ids.location_id, self.warehouse.lot_stock_id)

    def test_create_type_product_several_warehouses(self):
        new_warehouse = self.create_warehouse('NWH', self.user_company)
        self.user_company.warehouse_auto_orderpoint_ids = [
            (4, new_warehouse.id)]
        self.assertEqual(
            len(self.user_company.warehouse_auto_orderpoint_ids), 2)
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEqual(len(product.orderpoint_ids), 2)
        orderpoint_wh1 = product.orderpoint_ids.filtered(
            lambda op: op.warehouse_id == self.warehouse)
        self.assertEqual(len(orderpoint_wh1), 1)
        self.assertEqual(
            orderpoint_wh1.location_id, self.warehouse.lot_stock_id)
        orderpoint_wh2 = product.orderpoint_ids.filtered(
            lambda op: op.warehouse_id == new_warehouse)
        self.assertEqual(len(orderpoint_wh2), 1)
        self.assertEqual(
            orderpoint_wh2.location_id, new_warehouse.lot_stock_id)

    def test_create_type_product_no_warehouse(self):
        self.user_company.warehouse_auto_orderpoint_ids = [(6, 0, [])]
        self.assertEqual(
            len(self.user_company.warehouse_auto_orderpoint_ids), 0)
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEqual(len(product.orderpoint_ids), 0)

    def test_create_tmpl_no_variant_type_service(self):
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product',
            'type': 'service',
            'standard_price': 10.00,
            'company_id': False,
        })
        self.assertFalse(product_tmpl.product_variant_ids.orderpoint_ids)

    def test_create_tmpl_no_variant_type_product_one_warehouse(self):
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product',
            'type': 'product',
            'standard_price': 10.00,
            'company_id': False,
        })
        self.assertEqual(
            len(product_tmpl.product_variant_ids.orderpoint_ids), 1)
        self.assertEqual(
            product_tmpl.product_variant_ids.orderpoint_ids.warehouse_id,
            self.warehouse)
        self.assertEqual(
            product_tmpl.product_variant_ids.orderpoint_ids.location_id,
            self.warehouse.lot_stock_id)

    def test_create_tmpl_no_variant_type_product_several_warehouses(self):
        new_warehouse = self.create_warehouse('NWH', self.user_company)
        self.user_company.warehouse_auto_orderpoint_ids = [
            (4, new_warehouse.id)]
        self.assertEqual(
            len(self.user_company.warehouse_auto_orderpoint_ids), 2)
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product',
            'type': 'product',
            'standard_price': 10.00,
            'company_id': False,
        })
        self.assertEqual(
            len(product_tmpl.product_variant_ids.orderpoint_ids), 2)
        orderpoint_wh1 = (
            product_tmpl.product_variant_ids.orderpoint_ids.filtered(
                lambda op: op.warehouse_id == self.warehouse))
        self.assertEqual(len(orderpoint_wh1), 1)
        self.assertEqual(
            orderpoint_wh1.location_id, self.warehouse.lot_stock_id)
        orderpoint_wh2 = (
            product_tmpl.product_variant_ids.orderpoint_ids.filtered(
                lambda op: op.warehouse_id == new_warehouse))
        self.assertEqual(len(orderpoint_wh2), 1)
        self.assertEqual(
            orderpoint_wh2.location_id, new_warehouse.lot_stock_id)

    def test_create_tmpl_no_variant_type_product_no_warehouse(self):
        self.user_company.warehouse_auto_orderpoint_ids = [(6, 0, [])]
        self.assertEqual(
            len(self.user_company.warehouse_auto_orderpoint_ids), 0)
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product',
            'type': 'product',
            'standard_price': 10.00,
            'company_id': False,
        })
        self.assertEqual(
            len(product_tmpl.product_variant_ids.orderpoint_ids), 0)

    def test_create_tmpl_variants_type_product_one_warehouse(self):
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product',
            'type': 'product',
            'standard_price': 10.00,
            'company_id': False,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(product_tmpl.product_variant_ids), 3)
        for product in product_tmpl.product_variant_ids:
            self.assertEqual(len(product.orderpoint_ids), 1)
            self.assertEqual(
                product.orderpoint_ids.warehouse_id, self.warehouse)
            self.assertEqual(
                product.orderpoint_ids.location_id,
                self.warehouse.lot_stock_id)

    def test_create_tmpl_variants_type_product_several_warehouses(self):
        new_warehouse = self.create_warehouse('NWH', self.user_company)
        self.user_company.warehouse_auto_orderpoint_ids = [
            (4, new_warehouse.id)]
        self.assertEqual(
            len(self.user_company.warehouse_auto_orderpoint_ids), 2)
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product',
            'type': 'product',
            'standard_price': 10.00,
            'company_id': False,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(product_tmpl.product_variant_ids), 3)
        for product in product_tmpl.product_variant_ids:
            self.assertEqual(len(product.orderpoint_ids), 2)
            orderpoint_wh1 = product.orderpoint_ids.filtered(
                lambda op: op.warehouse_id == self.warehouse)
            self.assertEqual(len(orderpoint_wh1), 1)
            self.assertEqual(
                orderpoint_wh1.location_id, self.warehouse.lot_stock_id)
            orderpoint_wh2 = product.orderpoint_ids.filtered(
                lambda op: op.warehouse_id == new_warehouse)
            self.assertEqual(len(orderpoint_wh2), 1)
            self.assertEqual(
                orderpoint_wh2.location_id, new_warehouse.lot_stock_id)

    def test_create_tmpl_variants_type_product_no_warehouse(self):
        self.user_company.warehouse_auto_orderpoint_ids = [(6, 0, [])]
        self.assertEqual(
            len(self.user_company.warehouse_auto_orderpoint_ids), 0)
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product',
            'type': 'product',
            'standard_price': 10.00,
            'company_id': False,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(product_tmpl.product_variant_ids), 3)
        for product in product_tmpl.product_variant_ids:
            self.assertEqual(len(product.orderpoint_ids), 0)

    def test_multicompany_create_type_service(self):
        new_company = self.create_new_company()
        self.warehouse = self.env['stock.warehouse'].search([]).filtered(
            lambda wh: wh.company_id.id == new_company.id)
        self.assertEqual(len(self.warehouse), 1)
        new_company.warehouse_auto_orderpoint_ids = [
            (6, 0, self.warehouse.ids)]
        self.assertEqual(
            len(new_company.warehouse_auto_orderpoint_ids), 1)
        new_user = self.create_new_user(new_company)
        product = self.env['product.product'].with_user(new_user.id).create({
            'type': 'service',
            'company_id': False,
            'name': 'Test service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertFalse(product.orderpoint_ids)

    def test_multicompany_create_type_product_one_warehouse(self):
        new_company = self.create_new_company()
        self.warehouse = self.env['stock.warehouse'].search([]).filtered(
            lambda wh: wh.company_id.id == new_company.id)
        self.assertEqual(len(self.warehouse), 1)
        new_company.warehouse_auto_orderpoint_ids = [
            (6, 0, self.warehouse.ids)]
        self.assertEqual(
            len(new_company.warehouse_auto_orderpoint_ids), 1)
        new_user = self.create_new_user(new_company)
        product = self.env['product.product'].with_user(new_user.id).create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEqual(len(product.orderpoint_ids), 1)
        self.assertEqual(product.orderpoint_ids.warehouse_id, self.warehouse)
        self.assertEqual(
            product.orderpoint_ids.location_id, self.warehouse.lot_stock_id)

    def test_multicompany_create_type_product_several_warehouses(self):
        new_company = self.create_new_company()
        new_warehouse1 = self.create_warehouse('WH1', new_company)
        new_warehouse2 = self.create_warehouse('WH2', new_company)
        new_company.warehouse_auto_orderpoint_ids = [
            (6, 0, [new_warehouse1.id, new_warehouse2.id])]
        self.assertEqual(
            len(new_company.warehouse_auto_orderpoint_ids), 2)
        new_user = self.create_new_user(new_company)
        product = self.env['product.product'].with_user(new_user.id).create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEqual(len(product.orderpoint_ids), 2)
        orderpoint_wh1 = product.orderpoint_ids.filtered(
            lambda op: op.warehouse_id == new_warehouse1)
        self.assertEqual(len(orderpoint_wh1), 1)
        self.assertEqual(
            orderpoint_wh1.location_id, new_warehouse1.lot_stock_id)
        orderpoint_wh2 = product.orderpoint_ids.filtered(
            lambda op: op.warehouse_id == new_warehouse2)
        self.assertEqual(len(orderpoint_wh2), 1)
        self.assertEqual(
            orderpoint_wh2.location_id, new_warehouse2.lot_stock_id)

    def test_multicompany_only_one_company_configured(self):
        new_company = self.create_new_company()
        self.assertFalse(new_company.warehouse_auto_orderpoint_ids)
        new_user = self.create_new_user(new_company)
        configured_product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Configured company product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEqual(len(configured_product.orderpoint_ids), 1)
        self.assertEqual(
            configured_product.orderpoint_ids.warehouse_id.name, 'YourCompany')
        unconfigured_product = (
            self.env['product.product'].with_user(new_user.id).create({
                'type': 'product',
                'company_id': False,
                'name': 'Unconfigured company product',
                'standard_price': 10,
                'list_price': 100,
            }))
        self.assertFalse(unconfigured_product.orderpoint_ids)

    def test_multicompany_create_product_in_unconfigured_company(self):
        new_company = self.create_new_company()
        self.assertFalse(new_company.warehouse_auto_orderpoint_ids)
        new_user = self.create_new_user(self.user_company)
        new_user.write({
            'company_ids': [(6, 0, [self.user_company.id, new_company.id])],
            'company_id': self.user_company.id,
        })
        product_model = (
            self.env['product.product'].with_user(new_user.id).with_context(
                allowed_company_ids=[self.user_company.id, new_company.id])
            .with_company(self.user_company))
        self.assertEqual(product_model.env.company, self.user_company)
        with self.assertRaises(UserError) as error:
            product_model.create({
                'type': 'product',
                'company_id': new_company.id,
                'name': 'Unconfigured company product',
                'standard_price': 10,
                'list_price': 100,
            })
        error_message = re.sub(
            r'OP/\d+', 'OP/<product id>', str(error.exception))
        self.assertEqual(
            error_message,
            'Incompatible companies on records:\n'
            '- \'OP/<product id>\' belongs to company \'%s\' and \'Product\' '
            '(product_id: \'Unconfigured company product\') belongs to '
            'another company.' % self.user_company.name,
        )
