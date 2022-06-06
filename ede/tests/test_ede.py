###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestEde(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ede_supplier = self.env.ref('ede.res_partner_ede')
        self.customer = self.env['res.partner'].create({
            'name': 'Customer Test',
            'customer': True,
            'supplier': False,
        })
        self.company = self.env.user.company_id
        self.company.write({
            'ede_supplier_id': self.ede_supplier.id,
            'ede_user_id': self.env.user.id,
            'ede_real_wsdl':
                'https://webservices.ede.de:9443/ibis/ws/WS_EXT_ELC?wsdl',
            'ede_real_member': '400246',
            'ede_real_user': 'USER1',
            'ede_real_password': 'fdrt483Rrt',
            'ede_real_url_user': 'EDE_WS',
            'ede_real_url_password': 'Hf8e2R/vh)aaW2pL',
            'ede_runtime': 'real',
            'ede_picking_type_id': self.env.ref('stock.picking_type_in').id,
            'ede_start_code': '1982',

        })
        self.route_ede_customer = self.env.ref(
            'stock.route_warehouse0_mto').copy({
                'name': 'Ede Customer',
                'sale_selectable': True,
                'is_ede_customer': True,
            })
        self.route_ede_company = \
            self.route_ede_customer.copy({
                'name': 'Ede Company',
                'sale_selectable': True,
                'is_ede_company': True,
            })
        self.product_01 = self.env['product.product'].create({
            'type': 'product', 'company_id': self.env.user.company_id.id,
            'name': 'Llave de vaso allen 1/2" 10x 60mm inter. FORMAT',
            'default_code': '198261230100',
            'barcode': '4317784094610',
            'standard_price': 2.92, 'list_price': 6.08,
            # 'route_ids': [(6, 0, [self.route_ede_customer.id])],
            'seller_ids': [(0, 0, {'name': self.ede_supplier.id})],
        })

    def create_sale_order(self):
        order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'client_order_ref': 'XXX-YYY-ZZZ',
            'partner_shipping_id': self.customer.id,
        })
        self.env['sale.order.line'].create({
            'product_id': self.product_01.id,
            'product_uom_qty': 1.00,
            'route_id': self.route_ede_customer.id,
            'order_id': order.id,
        })
        return order

    def create_simulation_sale(self, order=None):
        return self.env['simulator.sale'].create({
            'order_id': order.id,
            'lines': [(0, 0, {
                'sale_line_id': order.order_line[0].id,
            })]
        })

    def create_simulation_purchase(self, order=None):
        return self.env['simulator.purchase'].create({
            'order_id': order.id,
            'lines': [(0, 0, {
                'purchase_line_id': order.order_line[0].id,
            })]
        })

    def test_ede_workflow(self):
        so = self.create_sale_order()
        self.assertEquals(
            so.state, 'draft', msg='Sale: Create and Not Draft State')
        self.assertTrue(so.order_line.filtered(
            lambda l: l.route_id == self.route_ede_customer),
            msg='Sale: Not ede route lines')
        so.action_confirm()
        self.assertEquals(so.state, 'sale', msg='Sale: State confirm Error')
        self.assertTrue(so.name, msg='Sale: Order not name')
        self.assertTrue(so.order_line[0].is_simulator,
                        msg='Sale: Order Line Not Is Simulator')
        self.assertEquals(so.order_line[0].state, 'sale',
                          msg='Sale: Line State confirm ok')
        simu_so = self.create_simulation_sale(so)
        self.assertTrue(
            simu_so, msg='Sale: Not Simulation Order, name:%s' % so.name)
        self.assertEquals(simu_so.state, 'step_1')
        simu_so.action_to_step_2()
        self.assertEquals(simu_so.state, 'step_2')
        po = self.env['purchase.order'].search([('sale_order_id', '=', so.id)])
        self.assertTrue(po, msg='Purchase: Not Order, name:%s' % so.name)
        self.assertEquals(po.state, 'draft')
        self.assertTrue(po.is_ede_order, 'Purchase: no purchase ede order')
        simu_po = self.create_simulation_purchase(po)
        self.assertTrue(
            simu_po, msg='Purchase: Not Simulation Order, name:%s' % po.name)
        self.assertEquals(simu_po.state, 'step_1')
        simu_po.action_to_step_2()
        self.assertEquals(simu_po.state, 'step_2')
        po.ede_document_id = '5514524421'
        po.ede_state = 'A'
        po.button_confirm()
        self.assertEqual(
            po.state, 'purchase', 'Purchase: PO state should be Purchase')
        self.assertEqual(po.picking_count, 1,
                         'Purchase: one picking should be created"')
        po.ede_check_status(po)
        self.assertEquals(po.ede_state, 'A')
