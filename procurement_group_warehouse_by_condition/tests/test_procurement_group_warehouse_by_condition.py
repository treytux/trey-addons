###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProcurementGroupWarehouseByCondition(TransactionCase):

    def setUp(self):
        super().setUp()
        self.activity_type_warn_id = (
            self.ref('mail.mail_activity_data_warning'))
        self.main_company = self.env.ref('base.main_company')
        self.company_2 = self.env['res.company'].create({
            'name': 'Company 2',
        })
        self.user = self.env['res.users'].create({
            'name': 'Test user',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.main_company.id])],
            'company_id': self.main_company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('sales_team.group_sale_manager').id,
            ])],
        })
        self.user.partner_id.email = self.user.login
        self.user_manager = self.env['res.users'].create({
            'name': 'Test user ,anager',
            'login': 'user_manager@test.com',
            'company_ids': [(6, 0, [self.main_company.id])],
            'company_id': self.main_company.id,
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_manager').id,
                self.env.ref('stock.group_stock_manager').id,
                self.env.ref('purchase.group_purchase_manager').id,
            ])],
        })
        self.user_manager.partner_id.email = self.user_manager.login
        self.customer = self.env['res.partner'].sudo(
            self.user.id).create({
                'name': 'Customer test',
                'customer': True,
                'company_id': False,
                'zip': '18008',
            })
        self.supplier = self.env['res.partner'].sudo(
            self.user.id).create({
                'name': 'Supplier test',
                'supplier': True,
                'company_id': False,
            })
        self.warehouse_by_condition = self.env.ref(
            'procurement_group_warehouse_by_condition.warehouse_by_condition')
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.warehouse_02 = self.create_warehouse('2', self.user_manager)
        self.warehouse_03 = self.create_warehouse('3', self.user_manager)
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.all_category = self.env.ref('product.product_category_all')
        self.product_01 = self.env['product.product'].sudo(
            self.user.id).create({
                'type': 'product',
                'company_id': False,
                'name': 'Test product 01',
                'standard_price': 90,
                'list_price': 100,
                'route_ids': [(6, 0, [self.buy_route.id])],
            })
        self.env['product.supplierinfo'].sudo(
            self.user.id).create({
                'name': self.supplier.id,
                'product_tmpl_id': self.product_01.product_tmpl_id.id,
                'price': 80,
            })
        self.product_02 = self.env['product.product'].sudo(
            self.user.id).create({
                'type': 'product',
                'company_id': False,
                'name': 'Test product 02',
                'standard_price': 90,
                'list_price': 100,
                'route_ids': [(6, 0, [self.buy_route.id])],
            })
        self.env['product.supplierinfo'].sudo(
            self.user.id).create({
                'name': self.supplier.id,
                'product_tmpl_id': self.product_02.product_tmpl_id.id,
                'price': 80,
            })
        self.product_03 = self.env['product.product'].sudo(
            self.user.id).create({
                'type': 'product',
                'company_id': False,
                'name': 'Test product 03',
                'standard_price': 90,
                'list_price': 100,
                'route_ids': [(6, 0, [self.buy_route.id])],
            })
        self.env['product.supplierinfo'].sudo(
            self.user.id).create({
                'name': self.supplier.id,
                'product_tmpl_id': self.product_03.product_tmpl_id.id,
                'price': 80,
            })

    def create_sale(self, product, quantity, warehouse, partner, user):
        return self.env['sale.order'].sudo(user.id).create({
            'partner_id': partner.id,
            'company_id': user.company_id.id,
            'warehouse_id': warehouse.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'price_unit': product.list_price,
                'product_uom_qty': quantity,
            })]
        })

    def create_warehouse(self, key, user):
        return self.env['stock.warehouse'].sudo(user.id).create({
            'name': 'Warehouse %s' % key,
            'code': 'WH%s' % key,
        })

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_normal_flow_without_warehouse_by_condition(self):
        self.update_qty_on_hand(
            self.product_01, self.stock_wh.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_01, 1, self.stock_wh, self.customer, self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(picking.picking_type_id, self.stock_wh.out_type_id)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 0)

    def test_conditionbyqty_with_stock_in_main_warehouse_variant(self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_without_stock_in_main_warehouse_variant(
            self):
        self.main_company.notification_user_id = self.user_manager.id
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_and_several_zip_variant(self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '28001, 14001',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '28001, 14001, 18008',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_and_zip_variant(self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_03.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_03.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_and_alternative_warehouse_with_stock_variant(self):
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product_01.with_context(
            location=self.warehouse_02.lot_stock_id.id).qty_available, 0)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': [
                            (6, 0, [self.stock_wh.id, self.warehouse_03.id])],
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_03.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_03.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_and_alternative_warehouse_without_stock_variant(
            self):
        self.main_company.notification_user_id = self.user_manager.id
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product_01.with_context(
            location=self.warehouse_02.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product_01.with_context(
            location=self.warehouse_03.lot_stock_id.id).qty_available, 0)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': [
                            (6, 0, [self.stock_wh.id, self.warehouse_03.id])],
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_constraint_warehouse_id_unique_variant(self):
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        with self.assertRaises(ValidationError) as result:
            self.env['procurement.group.warehouse_by_condition'].sudo(
                self.user_manager).create({
                    'warehouse_id': self.warehouse_by_condition.id,
                    'line_ids': [
                        (0, 0, {
                            'sequence': 1,
                            'applied_on': 'product_variant',
                            'product_id': self.product_02.id,
                            'sign': '>',
                            'quantity': 10,
                            'zips': '',
                            'main_warehouse_id': self.warehouse_03.id,
                            'alternative_warehouse_ids': False,
                        }),
                    ],
                })
        self.assertIn(
            'Another condition procurement group warehouse already exists for '
            'warehouse Warehouse by conditions.', result.exception.name)

    def test_constraint_zip_variant(self):
        with self.assertRaises(ValidationError) as result:
            self.env['procurement.group.warehouse_by_condition'].sudo(
                self.user_manager).create({
                    'warehouse_id': self.warehouse_by_condition.id,
                    'line_ids': [
                        (0, 0, {
                            'sequence': 1,
                            'applied_on': 'product_variant',
                            'product_id': self.product_02.id,
                            'sign': '>',
                            'quantity': 10,
                            'zips': '28008;18008',
                            'main_warehouse_id': self.warehouse_03.id,
                            'alternative_warehouse_ids': False,
                        }),
                    ],
                })
        self.assertIn(
            'Zips must contain only numbers and commas.',
            result.exception.name)

    def test_constraint_exist_line_ids(self):
        with self.assertRaises(ValidationError) as result:
            self.env['procurement.group.warehouse_by_condition'].sudo(
                self.user_manager).create({
                    'warehouse_id': self.warehouse_by_condition.id,
                    'line_ids': [],
                })
        self.assertIn(
            'You must add at least one condition line.', result.exception.name)

    def test_constraint_duplicate_line_ids_variant(self):
        with self.assertRaises(ValidationError) as result:
            self.env['procurement.group.warehouse_by_condition'].sudo(
                self.user_manager).create({
                    'warehouse_id': self.warehouse_by_condition.id,
                    'line_ids': [
                        (0, 0, {
                            'sequence': 1,
                            'applied_on': 'product_variant',
                            'product_id': self.product_01.id,
                            'sign': '>',
                            'quantity': 5,
                            'zips': '',
                            'main_warehouse_id': self.stock_wh.id,
                            'alternative_warehouse_ids': False,
                        }),
                        (0, 0, {
                            'sequence': 2,
                            'applied_on': 'product_variant',
                            'product_id': self.product_01.id,
                            'sign': '>',
                            'quantity': 5,
                            'zips': '',
                            'main_warehouse_id': self.stock_wh.id,
                            'alternative_warehouse_ids': False,
                        }),
                    ],
                })
        self.assertIn(
            'Condition line repeated for warehouse Warehouse by conditions. '
            'You can not more than one line with the same conditions.',
            result.exception.name)

    def test_constraint_alternative_whs_different_main_warehouse_variant(self):
        with self.assertRaises(ValidationError) as result:
            self.env['procurement.group.warehouse_by_condition'].sudo(
                self.user_manager).create({
                    'warehouse_id': self.warehouse_by_condition.id,
                    'line_ids': [
                        (0, 0, {
                            'sequence': 1,
                            'applied_on': 'product_variant',
                            'product_id': self.product_01.id,
                            'sign': '>',
                            'quantity': 5,
                            'zips': '',
                            'main_warehouse_id': self.stock_wh.id,
                            'alternative_warehouse_ids': [
                                (6, 0, [self.stock_wh.id])]
                        }),
                    ],
                })
        self.assertIn(
            'You cannot add the warehouse defined as the main warehouse to '
            'the same condition line as an alternative warehouse. Select a '
            'different warehouse(s).',
            result.exception.args[0])

    def test_conditionbyqty_and_zip_and_alternative_whs_with_stock_variant(
            self):
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': [
                            (6, 0, [self.stock_wh.id, self.warehouse_02.id])],
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_03.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_03.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_and_zip_and_alternative_whs_without_stock_variant(
            self):
        self.main_company.notification_user_id = self.user_manager.id
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product_01.with_context(
            location=self.warehouse_02.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product_01.with_context(
            location=self.warehouse_03.lot_stock_id.id).qty_available, 0)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': [
                            (6, 0, [self.stock_wh.id, self.warehouse_02.id])],
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_03.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_03.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_several_sale_lines_variant(self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_variant',
                        'product_id': self.product_02.id,
                        'sign': '>=',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.env['sale.order'].sudo(self.user.id).create({
            'partner_id': self.customer.id,
            'company_id': self.user.company_id.id,
            'warehouse_id': self.warehouse_by_condition.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 2,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_product_01 = sale.picking_ids.filtered(
            lambda pick: pick.product_id == self.product_01)
        self.assertEqual(len(picking_product_01), 1)
        self.assertEqual(
            picking_product_01.move_lines.location_id,
            self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking_product_01.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking_product_01.picking_type_id, self.warehouse_02.out_type_id)
        picking_product_02 = sale.picking_ids.filtered(
            lambda pick: pick.product_id == self.product_02)
        self.assertEqual(len(picking_product_02), 1)
        self.assertEqual(
            picking_product_02.move_lines.location_id,
            self.warehouse_03.lot_stock_id)
        self.assertEqual(
            picking_product_02.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking_product_02.picking_type_id, self.warehouse_03.out_type_id)
        picking_product_01.action_assign()
        self.assertEqual(picking_product_01.state, 'assigned')
        picking_product_02.action_assign()
        self.assertEqual(picking_product_02.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 2)

    def test_conditionbyqty_partial_stock_warehouses_01_variant(self):
        self.update_qty_on_hand(
            self.product_01, self.stock_wh.lot_stock_id, 1)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>=',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': [
                            (6, 0, self.warehouse_02.ids)],
                    }),
                ],
            })
        sale = self.env['sale.order'].sudo(self.user.id).create({
            'partner_id': self.customer.id,
            'company_id': self.user.company_id.id,
            'warehouse_id': self.warehouse_by_condition.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 3,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_stock_wh = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.stock_wh.lot_stock_id)
        self.assertEqual(len(picking_stock_wh), 1)
        self.assertEqual(len(picking_stock_wh.move_lines), 1)
        self.assertEqual(picking_stock_wh.move_lines.product_uom_qty, 1)
        picking_stock_wh_02 = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.warehouse_02.lot_stock_id)
        self.assertEqual(len(picking_stock_wh_02), 1)
        self.assertEqual(len(picking_stock_wh_02.move_lines), 1)
        self.assertEqual(picking_stock_wh_02.move_lines.product_uom_qty, 2)
        picking_stock_wh.action_assign()
        self.assertEqual(picking_stock_wh.state, 'assigned')
        picking_stock_wh_02.action_assign()
        self.assertEqual(picking_stock_wh_02.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_partial_stock_warehouses_02_variant(self):
        self.update_qty_on_hand(
            self.product_01, self.stock_wh.lot_stock_id, 1)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 1)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>=',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': [
                            (6, 0, [
                                self.warehouse_02.id, self.warehouse_03.id])],
                    }),
                ],
            })
        sale = self.env['sale.order'].sudo(self.user.id).create({
            'partner_id': self.customer.id,
            'company_id': self.user.company_id.id,
            'warehouse_id': self.warehouse_by_condition.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 3,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 3)
        picking_stock_wh = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.stock_wh.lot_stock_id)
        self.assertEqual(len(picking_stock_wh), 1)
        self.assertEqual(len(picking_stock_wh.move_lines), 1)
        self.assertEqual(picking_stock_wh.move_lines.product_uom_qty, 1)
        picking_stock_wh_02 = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.warehouse_02.lot_stock_id)
        self.assertEqual(len(picking_stock_wh_02), 1)
        self.assertEqual(len(picking_stock_wh_02.move_lines), 1)
        self.assertEqual(picking_stock_wh_02.move_lines.product_uom_qty, 1)
        picking_stock_wh_03 = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.warehouse_03.lot_stock_id)
        self.assertEqual(len(picking_stock_wh_03), 1)
        self.assertEqual(len(picking_stock_wh_03.move_lines), 1)
        self.assertEqual(picking_stock_wh_03.move_lines.product_uom_qty, 1)
        picking_stock_wh.action_assign()
        self.assertEqual(picking_stock_wh.state, 'assigned')
        picking_stock_wh_02.action_assign()
        self.assertEqual(picking_stock_wh_02.state, 'assigned')
        picking_stock_wh_03.action_assign()
        self.assertEqual(picking_stock_wh_03.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_partial_stock_warehouses_03_variant(self):
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 1)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 1)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>=',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': [
                            (6, 0, [
                                self.warehouse_02.id, self.warehouse_03.id])],
                    }),
                ],
            })
        sale = self.env['sale.order'].sudo(self.user.id).create({
            'partner_id': self.customer.id,
            'company_id': self.user.company_id.id,
            'warehouse_id': self.warehouse_by_condition.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 3,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 3)
        picking_stock_wh_02 = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.warehouse_02.lot_stock_id)
        self.assertEqual(len(picking_stock_wh_02), 1)
        self.assertEqual(len(picking_stock_wh_02.move_lines), 1)
        self.assertEqual(picking_stock_wh_02.move_lines.product_uom_qty, 1)
        picking_stock_wh_03 = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.warehouse_03.lot_stock_id)
        self.assertEqual(len(picking_stock_wh_03), 1)
        self.assertEqual(len(picking_stock_wh_03.move_lines), 1)
        self.assertEqual(picking_stock_wh_03.move_lines.product_uom_qty, 1)
        picking_stock_wh = sale.picking_ids.filtered(
            lambda pick: pick.location_id == self.stock_wh.lot_stock_id)
        self.assertEqual(len(picking_stock_wh), 1)
        self.assertEqual(len(picking_stock_wh.move_lines), 1)
        self.assertEqual(picking_stock_wh.move_lines.product_uom_qty, 1)
        picking_stock_wh_02.action_assign()
        self.assertEqual(picking_stock_wh_02.state, 'assigned')
        picking_stock_wh_03.action_assign()
        self.assertEqual(picking_stock_wh_03.state, 'assigned')
        picking_stock_wh.action_assign()
        self.assertEqual(picking_stock_wh.state, 'confirmed')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_conditionbyqty_no_satisfy_any_condition_variant(self):
        self.main_company.notification_user_id = self.user_manager.id
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.stock_wh.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', sale.id),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.assertIn(
            'No condition line found for warehouse \'Warehouse by '
            'conditions\' for the product \'Test product 01\' that matches '
            'the conditions', mail_activities.note)
        self.assertIn(
            'The company\'s default warehouse is assigned: \'YourCompany\'.',
            mail_activities.note)
        self.assertEquals(mail_activities.user_id, self.user_manager)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', (
                'No condition line found for warehouse \'Warehouse by '
                'conditions\' for the product \'Test product 01\' '
                'that matches the conditions')),
        ])
        self.assertEquals(len(mail_messages), 1)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 0)

    def test_conditionbyqty_no_satisfy_any_condition_zip_variant(self):
        self.main_company.notification_user_id = self.user_manager.id
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.stock_wh.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', sale.id),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.assertIn(
            'No condition line found for warehouse \'Warehouse by '
            'conditions\' for the product \'Test product 01\' that matches '
            'the conditions',
            mail_activities.note)
        self.assertIn(
            'The company\'s default warehouse is assigned: \'YourCompany\'.',
            mail_activities.note)
        self.assertEquals(mail_activities.user_id, self.user_manager)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', (
                'No condition line found for warehouse \'Warehouse by '
                'conditions\' for the product \'Test product 01\' that '
                'matches the conditions')),
        ])
        self.assertEquals(len(mail_messages), 1)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 0)

    def test_notificate_partner_shipping_without_zip_01_variant(self):
        self.main_company.notification_user_id = self.user_manager.id
        self.customer.zip = ''
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.stock_wh.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', sale.id),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.assertIn(
            'The partner shipping address does not have a zip code. The '
            'company\'s default warehouse is assigned: \'YourCompany\'',
            mail_activities.note)
        self.assertEquals(mail_activities.user_id, self.user_manager)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', (
                'The partner shipping address does not have a zip code. The '
                'company\'s default warehouse is assigned: \'YourCompany\'')),
        ])
        self.assertEquals(len(mail_messages), 1)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 0)

    def test_notificate_partner_shipping_without_zip_02_variant(self):
        self.main_company.notification_user_id = self.user_manager.id
        customer_02 = self.env['res.partner'].create({
            'name': 'Customer test 02',
            'company_type': 'company',
            'street': '123 Main Street',
            'city': 'Springfield',
            'zip': '18008',
            'child_ids': [(0, 0, {
                'name': 'Shipping Address',
                'type': 'delivery',
                'street': '456 Shipping Avenue',
                'city': 'Springfield',
                'zip': '',
            })]
        })
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '28001',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.partner_shipping_id = customer_02.child_ids[0].id
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.stock_wh.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', sale.id),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.assertIn(
            'The partner shipping address does not have a zip code. The '
            'company\'s default warehouse is assigned: \'YourCompany\'',
            mail_activities.note)
        self.assertEquals(mail_activities.user_id, self.user_manager)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', (
                'The partner shipping address does not have a zip code. The '
                'company\'s default warehouse is assigned: \'YourCompany\'')),
        ])
        self.assertEquals(len(mail_messages), 1)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 0)

    def test_multicompany_notification_user(self):
        self.main_company.notification_user_id = self.user.id
        self.user_manager.write({
            'company_ids': [(4, self.company_2.id)],
            'company_id': self.company_2.id,
        })
        self.company_2.notification_user_id = self.user_manager.id
        warehouse_by_condition_2 = self.create_warehouse(
            'WH by condition 2', self.user_manager)
        warehouse_by_condition_2.is_warehouse_by_condition = True
        warehouse_company_2 = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_2.id),
            ('is_warehouse_by_condition', '=', False),
        ])
        warehouse2_company_2 = self.create_warehouse('WH2', self.user_manager)
        self.assertEqual(len(warehouse_company_2), 1)
        self.assertEqual(self.product_01.sudo(self.user_manager).with_context(
            location=warehouse_company_2.lot_stock_id.id).qty_available, 0)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': warehouse_by_condition_2.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': warehouse_company_2.id,
                        'alternative_warehouse_ids': [
                            (6, 0, warehouse2_company_2.ids)],
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, warehouse_by_condition_2, self.customer,
            self.user_manager)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, warehouse_company_2.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, warehouse_company_2.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', sale.id),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.assertIn(
            'No condition line found for warehouse \'Warehouse WH by '
            'condition 2\' for the product \'Test product 01\' that matches '
            'the conditions',
            mail_activities.note)
        self.assertIn(
            'The company\'s default warehouse is assigned: \'Company 2\'.',
            mail_activities.note)
        self.assertEquals(mail_activities.user_id, self.user_manager)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', (
                'No condition line found for warehouse \'Warehouse WH by '
                'condition 2\' for the product \'Test product 01\' that '
                'matches the conditions')),
        ])
        self.assertEquals(len(mail_messages), 1)
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 0)

    def test_apply_condition_with_mto_route(self):
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.product_01.route_ids = [(4, self.mto_route.id)]
        self.assertIn(self.mto_route, self.product_01.route_ids)
        self.assertIn(self.buy_route, self.product_01.route_ids)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition,
            self.customer, self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEqual(len(picking_out.move_lines), 1)
        self.assertEqual(picking_out.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking_out.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking_out.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking_out.picking_type_id, self.warehouse_02.out_type_id)
        purchase = self.env['purchase.order'].search([
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.order_line.product_id, self.product_01)
        purchase.button_confirm()
        self.assertEqual(purchase.state, 'purchase')
        picking_in = purchase.picking_ids
        self.assertEqual(len(picking_in.move_lines), 1)
        self.assertEqual(picking_in.move_lines.product_id, self.product_01)
        self.assertEqual(picking_in.move_lines.location_id, self.supplier_loc)
        self.assertEqual(
            picking_in.move_lines.location_dest_id,
            self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking_in.picking_type_id, self.warehouse_02.in_type_id)
        picking_in.action_assign()
        self.assertEqual(picking_in.state, 'assigned')
        for move in picking_in.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in.action_done()
        self.assertEqual(picking_in.state, 'done')
        picking_out.action_assign()
        self.assertEqual(picking_out.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 1)

    def test_not_apply_condition_dropshipping_route(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_dropshipping'),
        ])
        if module.state != 'installed':
            self.skipTest(
                'Module \'stock_dropshipping\' not installed, ignore test.')
        dropshipping_type = self.env.ref(
            'stock_dropshipping.picking_type_dropship')
        dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
        product_dropshipping = self.env['product.product'].create({
            'name': 'Test product dropshipping',
            'type': 'product',
            'route_ids': [(6, 0, [dropshipping_route.id])],
            'seller_ids': [
                (0, 0, {
                    'name': self.supplier.id,
                    'price': 10,
                }),
            ],
        })
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': product_dropshipping.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': product_dropshipping.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            product_dropshipping, 1, self.warehouse_by_condition,
            self.customer, self.user)
        sale.action_confirm()
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.order_line.product_id, product_dropshipping)
        purchase.button_confirm()
        self.assertEqual(purchase.state, 'purchase')
        picking = purchase.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, product_dropshipping)
        self.assertEqual(picking.move_lines.location_id, self.supplier_loc)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(picking.picking_type_id, dropshipping_type)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEquals(len(mail_messages), 0)

    def test_inactive_stock_picking_type_for_is_warehouse_by_condition(self):
        picking_types = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse_by_condition.id),
        ])
        self.assertFalse(picking_types)
        new_warehouse = self.create_warehouse('NEW', self.user_manager)
        self.assertFalse(new_warehouse.is_warehouse_by_condition)
        picking_types = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', new_warehouse.id),
        ])
        self.assertTrue(picking_types)
        new_warehouse.is_warehouse_by_condition = True
        self.assertTrue(new_warehouse.is_warehouse_by_condition)
        picking_types = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', new_warehouse.id),
        ])
        self.assertFalse(picking_types)
        new_warehouse.is_warehouse_by_condition = False
        self.assertFalse(new_warehouse.is_warehouse_by_condition)
        picking_types = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', new_warehouse.id),
        ])
        self.assertTrue(picking_types)

    def test_condition_equal(self):
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '==',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(picking.picking_type_id, self.stock_wh.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'confirmed')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEqual(len(mail_messages), 1)

    def test_conditionbyqty_with_stock_in_main_warehouse_template(self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_template',
                        'product_tmpl_id': self.product_01.product_tmpl_id.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_template',
                        'product_tmpl_id': self.product_01.product_tmpl_id.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEqual(len(mail_messages), 1)
        self.assertIn('Product template', mail_messages.body)

    def test_conditionbyqty_with_stock_in_main_warehouse_diff_applied_on_01(
            self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_template',
                        'product_tmpl_id': self.product_01.product_tmpl_id.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEqual(len(mail_messages), 1)
        self.assertIn('Product variant', mail_messages.body)

    def test_conditionbyqty_with_stock_in_main_warehouse_diff_applied_on_02(
            self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_global',
                        'sign': '>',
                        'quantity': 0,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_template',
                        'product_tmpl_id': self.product_01.product_tmpl_id.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_03.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_03.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEqual(len(mail_messages), 1)
        self.assertIn('All products', mail_messages.body)

    def test_conditionbyqty_with_stock_in_main_warehouse_diff_applied_on_03(
            self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_template',
                        'product_tmpl_id': self.product_01.product_tmpl_id.id,
                        'sign': '>',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_global',
                        'sign': '>',
                        'quantity': 0,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEqual(len(mail_messages), 1)
        self.assertIn('Product variant', mail_messages.body)

    def test_conditionbyqty_with_stock_in_main_warehouse_diff_applied_on_04(
            self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_03.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_category',
                        'product_category_id': self.all_category.id,
                        'sign': '>',
                        'quantity': 0,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_template',
                        'product_tmpl_id': self.product_01.product_tmpl_id.id,
                        'sign': '>',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_03.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_03.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEqual(len(mail_messages), 1)
        self.assertIn('Product category', mail_messages.body)

    def test_conditionbyqty_with_stock_in_main_warehouse_diff_applied_on_05(
            self):
        self.update_qty_on_hand(
            self.product_01, self.warehouse_02.lot_stock_id, 10)
        self.env['procurement.group.warehouse_by_condition'].sudo(
            self.user_manager).create({
                'warehouse_id': self.warehouse_by_condition.id,
                'line_ids': [
                    (0, 0, {
                        'sequence': 1,
                        'applied_on': 'product_template',
                        'product_tmpl_id': self.product_01.product_tmpl_id.id,
                        'sign': '>',
                        'quantity': 1,
                        'zips': '',
                        'main_warehouse_id': self.stock_wh.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 2,
                        'applied_on': 'product_variant',
                        'product_id': self.product_01.id,
                        'sign': '<=',
                        'quantity': 5,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_02.id,
                        'alternative_warehouse_ids': False,
                    }),
                    (0, 0, {
                        'sequence': 3,
                        'applied_on': 'product_category',
                        'product_category_id': self.all_category.id,
                        'sign': '>',
                        'quantity': 0,
                        'zips': '',
                        'main_warehouse_id': self.warehouse_03.id,
                        'alternative_warehouse_ids': False,
                    }),
                ],
            })
        sale = self.create_sale(
            self.product_01, 1, self.warehouse_by_condition, self.customer,
            self.user)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_id, self.product_01)
        self.assertEqual(
            picking.move_lines.location_id, self.warehouse_02.lot_stock_id)
        self.assertEqual(
            picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            picking.picking_type_id, self.warehouse_02.out_type_id)
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        mail_messages = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('body', 'ilike', 'Procurement group warehouse by conditions:'),
        ])
        self.assertEqual(len(mail_messages), 1)
        self.assertIn('Product variant', mail_messages.body)
