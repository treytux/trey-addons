# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestSaleToPurchaseWizard(common.TransactionCase):

    def setUp(self):
        super(TestSaleToPurchaseWizard, self).setUp()

        base_pricelist_id = self.ref('product.list0')
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'customer': True})
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Supplier 01',
            'supplier': True})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': 100})
        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'pricelist_id': base_pricelist_id,
            'order_policy': 'picking',
            'order_line': [
                (0, 0, {'product_id': self.pp_01.id,
                        'product_uom_qty': 1.0})]})
        self.order_02 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'pricelist_id': base_pricelist_id,
            'order_policy': 'picking',
            'order_line': [
                (0, 0, {'product_id': self.pp_01.id,
                        'product_uom_qty': 1.0})]})
        self.order_03 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'pricelist_id': base_pricelist_id,
            'order_policy': 'picking',
            'order_line': [
                (0, 0, {'product_id': self.pp_01.id,
                        'product_uom_qty': 10.0})]})
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.inventory_loss = self.env.ref('stock.location_inventory')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)

    def test_01_without_product_supplierinfo(self):
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': True,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.customer_01.id)])
        self.assertEqual(len(purchases), 0)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)

    def test_02_orders_01_02_stock_checked_virtual(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': True,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'stock': True,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_02])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)

    def test_03_orders_01_03_stock_checked_virtual(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': True,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'stock': True,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_03])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 2)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 9)
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 10)

    def test_04_orders_01_02_stock_checked_virtual_with_virtual_negative(self):
        move_out = self.env['stock.move'].create({
            'name': self.pp_01.name,
            'product_id': self.pp_01.id,
            'product_uom_qty': 5,
            'product_uom': self.pp_01.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.inventory_loss.id})
        move_out.action_confirm()
        move_out.force_assign()
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, -5)
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': True,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, -5)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 6)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'stock': True,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_03])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 2)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 9)
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 10)

    def test_05_orders_01_02_stock_checked_real(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': True,
                'stock_type': 'real'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        picking_in.do_transfer()
        self.assertEqual(picking_in.state, 'done')
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'stock': True,
                'stock_type': 'real'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_02])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 1)

    def test_06_orders_01_03_stock_checked_real(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': True,
                'stock_type': 'real'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        picking_in.do_transfer()
        self.assertEqual(picking_in.state, 'done')
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'stock': True,
                'stock_type': 'real'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_03])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 2)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 1)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 9)
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 10)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        picking_in.do_transfer()
        self.assertEqual(picking_in.state, 'done')
        self.assertEqual(product_01.qty_available, 10)
        self.assertEqual(product_01.virtual_available, 10)

    def test_07_orders_01_02_stock_checked_real_with_real_negative(self):
        move_out = self.env['stock.move'].create({
            'name': self.pp_01.name,
            'product_id': self.pp_01.id,
            'product_uom_qty': 5,
            'product_uom': self.pp_01.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.inventory_loss.id})
        move_out.action_confirm()
        move_out.force_assign()
        move_out.action_done()
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, -5)
        self.assertEqual(product_01.virtual_available, -5)
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': True,
                'stock_type': 'real'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, -5)
        self.assertEqual(product_01.virtual_available, -5)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 6)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, -5)
        self.assertEqual(product_01.virtual_available, 1)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        picking_in.do_transfer()
        self.assertEqual(picking_in.state, 'done')
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'stock': True,
                'stock_type': 'real'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_03])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 2)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 1)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 9)
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 10)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        picking_in.do_transfer()
        self.assertEqual(picking_in.state, 'done')
        self.assertEqual(product_01.qty_available, 10)
        self.assertEqual(product_01.virtual_available, 10)

    def test_08_without_product_supplierinfo(self):
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': False,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.customer_01.id)])
        self.assertEqual(len(purchases), 0)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)

    def test_09_orders_01_02_stock_unchecked_virtual(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': False,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'stock': False,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_02])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 2)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        picking_in.do_transfer()
        self.assertEqual(picking_in.state, 'done')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 1)
        self.assertEqual(product_01.virtual_available, 1)

    def test_10_orders_01_03_stock_unchecked_virtual(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': False,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 0)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'stock': False,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_03])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 2)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 1)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 10)
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 11)

    def test_11_orders_01_02_stock_unchecked_virtual_with_virt_negative(self):
        move_out = self.env['stock.move'].create({
            'name': self.pp_01.name,
            'product_id': self.pp_01.id,
            'product_uom_qty': 5,
            'product_uom': self.pp_01.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.inventory_loss.id})
        move_out.action_confirm()
        move_out.force_assign()
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, -5)
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id})
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'stock': False,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_01])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)])
        self.assertEqual(len(purchases), 1)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, -5)
        purchase = purchases[0]
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 1)
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, -4)
        wiz = self.env['wiz.sale_order_to_purchase_order'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'stock': False,
                'stock_type': 'virtual'})
        wiz.button_purchase_view()
        products = wiz.get_products_from_orders([self.order_03])
        groupby_partner = wiz.groupby_partner(products)
        wiz.with_context(partner_list=[
            p for p in groupby_partner.keys()]).button_create_purchase()
        purchases = self.env['purchase.order'].search([(
            'partner_id', '=', self.supplier_01.id)], order='id desc')
        self.assertEqual(len(purchases), 2)
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, -4)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_qty, 10)
        purchase.signal_workflow('purchase_confirm')
        self.assertEqual(purchase.state, 'approved')
        product_01 = self.env['product.product'].with_context(
            location=self.stock_location.id).browse(self.pp_01.id)
        self.assertEqual(product_01.qty_available, 0)
        self.assertEqual(product_01.virtual_available, 6)
