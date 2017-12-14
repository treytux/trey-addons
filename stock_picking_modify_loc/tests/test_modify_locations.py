# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase
from openerp import exceptions


class TestModifyLocations(TransactionCase):

    def setUp(self):
        super(TestModifyLocations, self).setUp()
        self.taxs_21 = self.env['account.tax'].search([
            ('name', 'like', '%21%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_21.exists():
            raise exceptions.Warning(
                'Does not exist any account tax with \'21\' in name.')
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id})
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'product'})
        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id})
        wh = self.env['stock.warehouse'].search([
            ('company_id', '=', self.ref('base.main_company'))])
        if not wh.exists():
            raise exceptions.Warning(
                'Does not exist any warehouse for main company.')
        picking_data = {
            'partner_id': self.partner_01.id,
            'company_id': self.ref('base.main_company')}
        move_01_data = {
            'product_id': self.pp_01.id,
            'name': self.pp_01.name_template,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit')}
        move_02_data = {
            'product_id': self.pp_02.id,
            'name': self.pp_02.name_template,
            'product_uom_qty': 3,
            'product_uom': self.ref('product.product_uom_unit')}
        picking_out_data = picking_data.copy()
        picking_out_data.update({'picking_type_id': wh[0].out_type_id.id})
        self.picking_out = self.env['stock.picking'].create(picking_out_data)
        move_01_out_data = move_01_data.copy()
        move_01_out_data.update({
            'picking_id': self.picking_out.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_customers')})
        self.move_01_out = self.env['stock.move'].create(move_01_out_data)
        move_02_out_data = move_02_data.copy()
        move_02_out_data.update({
            'picking_id': self.picking_out.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_customers')})
        self.move_02_out = self.env['stock.move'].create(move_02_out_data)
        picking_in_data = picking_data.copy()
        picking_in_data.update({'picking_type_id': wh[0].in_type_id.id})
        self.picking_in = self.env['stock.picking'].create(picking_in_data)
        move_01_in_data = move_01_data.copy()
        move_01_in_data.update({
            'picking_id': self.picking_in.id,
            'location_id': self.ref('stock.stock_location_suppliers'),
            'location_dest_id': self.ref('stock.stock_location_stock')})
        self.move_01_in = self.env['stock.move'].create(move_01_in_data)
        move_02_in_data = move_02_data.copy()
        move_02_in_data.update({
            'picking_id': self.picking_in.id,
            'location_id': self.ref('stock.stock_location_suppliers'),
            'location_dest_id': self.ref('stock.stock_location_stock')})
        self.move_02_in = self.env['stock.move'].create(move_02_in_data)
        picking_inter_data = picking_data.copy()
        picking_inter_data.update({'picking_type_id': wh[0].int_type_id.id})
        self.picking_inter = self.env['stock.picking'].create(
            picking_inter_data)
        move_01_inter_data = move_01_data.copy()
        move_01_inter_data.update({
            'picking_id': self.picking_inter.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_scrapped')})
        self.move_01_inter = self.env['stock.move'].create(move_01_inter_data)
        move_02_inter_data = move_02_data.copy()
        move_02_inter_data.update({
            'picking_id': self.picking_inter.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_scrapped')})
        self.move_02_inter = self.env['stock.move'].create(move_02_inter_data)

    def test_modify_locations_out_draft(self):
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_orig_out_id': self.ref(
                    'stock.stock_location_customers'),
                'location_dest_out_id': self.ref(
                    'stock.stock_location_stock')})
        wiz.action_accept()
        self.assertEqual(self.move_01_out.location_id.id, self.ref(
            'stock.stock_location_customers'))
        self.assertEqual(self.move_02_out.location_id.id, self.ref(
            'stock.stock_location_customers'))
        self.assertEqual(self.move_01_out.location_dest_id.id, self.ref(
            'stock.stock_location_stock'))
        self.assertEqual(self.move_02_out.location_dest_id.id, self.ref(
            'stock.stock_location_stock'))

    def test_modify_locations_in_draft(self):
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_in.id],
            'active_id': self.picking_in.id}).create({
                'location_orig_in_id': self.ref(
                    'stock.stock_location_stock'),
                'location_dest_in_id': self.ref(
                    'stock.stock_location_suppliers')})
        wiz.action_accept()
        self.assertEqual(self.move_01_in.location_id.id, self.ref(
            'stock.stock_location_stock'))
        self.assertEqual(self.move_02_in.location_id.id, self.ref(
            'stock.stock_location_stock'))
        self.assertEqual(self.move_01_in.location_dest_id.id, self.ref(
            'stock.stock_location_suppliers'))
        self.assertEqual(self.move_02_in.location_dest_id.id, self.ref(
            'stock.stock_location_suppliers'))

    def test_modify_locations_internal_draft(self):
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_inter.id],
            'active_id': self.picking_inter.id}).create({
                'location_orig_in_id': self.ref(
                    'stock.stock_location_scrapped'),
                'location_dest_in_id': self.ref(
                    'stock.stock_location_stock')})
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_out_confirm(self):
        self.picking_out.action_confirm()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_orig_out_id': self.ref(
                    'stock.stock_location_customers'),
                'location_dest_out_id': self.ref(
                    'stock.stock_location_stock')})
        wiz.action_accept()
        self.assertEqual(self.move_01_out.location_id.id, self.ref(
            'stock.stock_location_customers'))
        self.assertEqual(self.move_02_out.location_id.id, self.ref(
            'stock.stock_location_customers'))
        self.assertEqual(self.move_01_out.location_dest_id.id, self.ref(
            'stock.stock_location_stock'))
        self.assertEqual(self.move_02_out.location_dest_id.id, self.ref(
            'stock.stock_location_stock'))

    def test_modify_locations_out_done(self):
        self.picking_out.action_confirm()
        self.picking_out.action_done()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_orig_out_id': self.ref(
                    'stock.stock_location_customers'),
                'location_dest_out_id': self.ref(
                    'stock.stock_location_stock')})
        self.assertRaises(Exception, wiz.action_accept)
