###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestSalePurchaseServiceGroupType(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier partner #1',
            'supplier': True,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer partner #1',
            'customer': True,
        })
        self.product_service_no = self.env['product.product'].create({
            'name': 'Test purchase Service product normal',
            'type': 'service',
            'service_to_purchase': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 100.0,
            'list_price': 200.0,
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 100.00,
                'delay': 0,
            })]
        })
        self.product_service_un = self.env['product.product'].create({
            'name': 'Test purchase service product ',
            'type': 'service',
            'service_to_purchase': True,
            'purchase_service_group_type': 'ungrouped',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 100.0,
            'list_price': 200.0,
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 100.00,
                'delay': 0,
            })]
        })
        self.product_service_dat = self.env['product.product'].create({
            'name': 'Test purchase service product',
            'type': 'service',
            'service_to_purchase': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 100.0,
            'list_price': 200.0,
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 100.00,
                'delay': 0,
            })],
            'purchase_service_group_type': 'ungrouped',
            'purchase_group_day': 15,
        })

    def test_normal_order(self):
        self.sale_order_no1 = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.so_line_no1 = self.env['sale.order.line'].create({
            'order_id': self.sale_order_no1.id,
            'product_id': self.product_service_no.id,
            'name': 'Service product normal',
            'product_uom_qty': 1,
            'product_uom': self.product_service_no.uom_id.id,
            'price_unit': self.product_service_no.list_price,
        })
        self.sale_order_no1.action_confirm()
        self.assertEquals(self.sale_order_no1.state, 'sale')
        self.assertTrue(self.so_line_no1.purchase_line_ids)
        self.sale_order_no2 = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.so_line_no2 = self.env['sale.order.line'].create({
            'order_id': self.sale_order_no2.id,
            'product_id': self.product_service_no.id,
            'name': 'Service product normal',
            'product_uom_qty': 1.0,
            'product_uom': self.product_service_no.uom_id.id,
            'price_unit': self.product_service_no.list_price,
        })
        self.sale_order_no2.action_confirm()
        self.assertEquals(self.sale_order_no2.state, 'sale')
        self.assertTrue(self.so_line_no2.purchase_line_ids)
        self.assertTrue(
            self.so_line_no2.purchase_line_ids,
            self.so_line_no1.purchase_line_ids,
        )

    def test_ungroup_order(self):
        self.sale_order_no1 = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.so_line_no1 = self.env['sale.order.line'].create({
            'order_id': self.sale_order_no1.id,
            'product_id': self.product_service_no.id,
            'name': 'Service product normal',
            'product_uom_qty': 1,
            'product_uom': self.product_service_no.uom_id.id,
            'price_unit': self.product_service_no.list_price,
        })
        self.sale_order_no1.action_confirm()
        self.assertEquals(self.sale_order_no1.state, 'sale')
        self.assertTrue(self.so_line_no1.purchase_line_ids)
        self.sale_order_un = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.so_line_un = self.env['sale.order.line'].create({
            'order_id': self.sale_order_un.id,
            'product_id': self.product_service_un.id,
            'name': 'Service product normal',
            'product_uom_qty': 1.0,
            'product_uom': self.product_service_un.uom_id.id,
            'price_unit': self.product_service_un.list_price,
        })
        self.sale_order_un.action_confirm()
        self.assertEquals(self.sale_order_un.state, 'sale')
        self.assertTrue(self.so_line_un.purchase_line_ids)
        self.assertNotEquals(self.so_line_un.purchase_line_ids,
                             self.so_line_no1.purchase_line_ids)
        self.assertNotEquals(self.so_line_un.purchase_line_ids[0].order_id,
                             self.so_line_no1.purchase_line_ids[0].order_id)

    def test_group_order_by_date(self):
        date_now = fields.Date.from_string(fields.Date.today())
        self.sale_order_no1 = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.so_line_no1 = self.env['sale.order.line'].create({
            'order_id': self.sale_order_no1.id,
            'product_id': self.product_service_dat.id,
            'name': 'Service product normal',
            'product_uom_qty': 1,
            'product_uom': self.product_service_dat.uom_id.id,
            'price_unit': self.product_service_dat.list_price,
        })
        self.sale_order_no1.action_confirm()
        self.assertEquals(self.sale_order_no1.state, 'sale')
        self.assertTrue(self.so_line_no1.purchase_line_ids)
        purchase_order = self.so_line_no1.purchase_line_ids[0].order_id
        self.assertTrue(purchase_order)
        self.assertEquals(purchase_order.date_order.date(), date_now)
        self.assertEquals(purchase_order.date_order.date().day, date_now.day)
        self.sale_order_dat1 = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.so_line_dat1 = self.env['sale.order.line'].create({
            'order_id': self.sale_order_dat1.id,
            'product_id': self.product_service_dat.id,
            'name': 'Service product normal',
            'product_uom_qty': 1.0,
            'product_uom': self.product_service_dat.uom_id.id,
            'price_unit': self.product_service_dat.list_price,
        })
        self.sale_order_dat1.action_confirm()
        self.assertEquals(self.sale_order_dat1.state, 'sale')
        self.assertTrue(self.so_line_dat1.purchase_line_ids)
        self.assertNotEquals(
            self.so_line_dat1.purchase_line_ids[0].order_id,
            self.so_line_no1.purchase_line_ids[0].order_id)
        _log.warning('Pedido normal: %s Pedido agrupado por fecha: %s' % (
            self.so_line_no1.purchase_line_ids[0].order_id.date_order,
            self.so_line_dat1.purchase_line_ids[0].order_id.date_order))
