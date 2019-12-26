# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase
from openerp import exceptions


class TestModifyLocations(TransactionCase):

    def setUp(self):
        super(TestModifyLocations, self).setUp()
        self.customer_loc_id = self.ref('stock.stock_location_customers')
        self.customer_loc = self.env['stock.location'].browse(
            self.customer_loc_id)
        self.supplier_loc_id = self.ref('stock.stock_location_suppliers')
        self.supplier_loc = self.env['stock.location'].browse(
            self.supplier_loc_id)
        self.stock_loc_id = self.ref('stock.stock_location_stock')
        self.stock_loc = self.env['stock.location'].browse(self.stock_loc_id)
        self.inventory_loss_loc_id = self.ref('stock.location_inventory')
        self.inventory_loss_loc = self.env['stock.location'].browse(
            self.inventory_loss_loc_id)
        self.transit_inter_loc_id = self.ref('stock.stock_location_inter_wh')
        self.transit_inter_loc = self.env['stock.location'].browse(
            self.transit_inter_loc_id)
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522',
        })
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product',
        })
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
        })
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'product',
        })
        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id,
        })
        wh = self.env['stock.warehouse'].search([
            ('company_id', '=', self.ref('base.main_company'))
        ])
        if not wh.exists():
            raise exceptions.Warning(
                'Does not exist any warehouse for main company.')
        picking_data = {
            'partner_id': self.partner_01.id,
            'company_id': self.ref('base.main_company'),
        }
        move_01_data = {
            'product_id': self.pp_01.id,
            'name': self.pp_01.name_template,
            'product_uom_qty': 10,
            'product_uom': self.ref('product.product_uom_unit'),
        }
        move_02_data = {
            'product_id': self.pp_02.id,
            'name': self.pp_02.name_template,
            'product_uom_qty': 30,
            'product_uom': self.ref('product.product_uom_unit'),
        }
        picking_out_data = picking_data.copy()
        picking_out_data.update({'picking_type_id': wh[0].out_type_id.id})
        self.picking_out = self.env['stock.picking'].create(picking_out_data)
        move_01_out_data = move_01_data.copy()
        move_01_out_data.update({
            'picking_id': self.picking_out.id,
            'location_id': self.stock_loc_id,
            'location_dest_id': self.customer_loc_id,
        })
        self.move_01_out = self.env['stock.move'].create(move_01_out_data)
        move_02_out_data = move_02_data.copy()
        move_02_out_data.update({
            'picking_id': self.picking_out.id,
            'location_id': self.stock_loc_id,
            'location_dest_id': self.customer_loc_id,
        })
        self.move_02_out = self.env['stock.move'].create(move_02_out_data)
        picking_in_data = picking_data.copy()
        picking_in_data.update({'picking_type_id': wh[0].in_type_id.id})
        self.picking_in = self.env['stock.picking'].create(picking_in_data)
        move_01_in_data = move_01_data.copy()
        move_01_in_data.update({
            'picking_id': self.picking_in.id,
            'location_id': self.supplier_loc_id,
            'location_dest_id': self.stock_loc_id,
        })
        self.move_01_in = self.env['stock.move'].create(move_01_in_data)
        move_02_in_data = move_02_data.copy()
        move_02_in_data.update({
            'picking_id': self.picking_in.id,
            'location_id': self.supplier_loc_id,
            'location_dest_id': self.stock_loc_id,
        })
        self.move_02_in = self.env['stock.move'].create(move_02_in_data)
        picking_inter_data = picking_data.copy()
        picking_inter_data.update({'picking_type_id': wh[0].int_type_id.id})
        self.picking_inter = self.env['stock.picking'].create(
            picking_inter_data)
        move_01_inter_data = move_01_data.copy()
        move_01_inter_data.update({
            'picking_id': self.picking_inter.id,
            'location_id': self.stock_loc_id,
            'location_dest_id': self.inventory_loss_loc_id,
        })
        self.move_01_inter = self.env['stock.move'].create(move_01_inter_data)
        move_02_inter_data = move_02_data.copy()
        move_02_inter_data.update({
            'picking_id': self.picking_inter.id,
            'location_id': self.stock_loc_id,
            'location_dest_id': self.inventory_loss_loc_id,
        })
        self.move_02_inter = self.env['stock.move'].create(move_02_inter_data)

    def get_real_stock(self, product, location):
        qty_product_dict = product.with_context(
            location=location.id)._product_available()
        return qty_product_dict[product.id]['qty_available']

    def update_stock(self, product, location, qty, lot=None):
        wiz = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': qty,
            'location_id': location.id,
            'lot_id': lot and lot.id or None,
        })
        wiz.change_product_qty()
        qty_stock = self.get_real_stock(product, location)
        self.assertEqual(qty_stock, qty)

    def test_modify_locations_out_draft(self):
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
            })
        wiz.action_accept()
        self.assertEqual(self.move_01_out.location_id, self.inventory_loss_loc)
        self.assertEqual(self.move_02_out.location_id, self.inventory_loss_loc)
        self.assertEqual(self.move_01_out.location_dest_id, self.customer_loc)
        self.assertEqual(self.move_02_out.location_dest_id, self.customer_loc)

    def test_modify_locations_in_draft(self):
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_in.id],
            'active_id': self.picking_in.id}).create({
                'location_dest_id': self.inventory_loss_loc_id,
            })
        wiz.action_accept()
        self.assertEqual(self.move_01_in.location_id, self.supplier_loc)
        self.assertEqual(self.move_02_in.location_id, self.supplier_loc)
        self.assertEqual(
            self.move_01_in.location_dest_id, self.inventory_loss_loc)
        self.assertEqual(
            self.move_02_in.location_dest_id, self.inventory_loss_loc)

    def test_modify_locations_internal_draft(self):
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_inter.id],
            'active_id': self.picking_inter.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
                'location_dest_id': self.transit_inter_loc_id,
            })
        wiz.action_accept()
        self.assertEqual(
            self.move_01_inter.location_id, self.inventory_loss_loc)
        self.assertEqual(
            self.move_02_inter.location_id, self.inventory_loss_loc)
        self.assertEqual(
            self.move_01_inter.location_dest_id, self.transit_inter_loc)
        self.assertEqual(
            self.move_02_inter.location_dest_id, self.transit_inter_loc)

    def test_modify_locations_out_confirm(self):
        self.picking_out.action_confirm()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
            })
        wiz.action_accept()
        self.assertEqual(self.move_01_out.location_id, self.inventory_loss_loc)
        self.assertEqual(self.move_02_out.location_id, self.inventory_loss_loc)
        self.assertEqual(self.move_01_out.location_dest_id, self.customer_loc)
        self.assertEqual(self.move_02_out.location_dest_id, self.customer_loc)

    def test_modify_locations_internal_confirm(self):
        self.picking_inter.action_confirm()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_inter.id],
            'active_id': self.picking_inter.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
                'location_dest_id': self.transit_inter_loc_id,
            })
        wiz.action_accept()
        self.assertEqual(
            self.move_01_inter.location_id, self.inventory_loss_loc)
        self.assertEqual(
            self.move_02_inter.location_id, self.inventory_loss_loc)
        self.assertEqual(
            self.move_01_inter.location_dest_id, self.transit_inter_loc)
        self.assertEqual(
            self.move_02_inter.location_dest_id, self.transit_inter_loc)

    def test_modify_locations_out_partially_available(self):
        self.update_stock(self.pp_01, self.stock_loc, 1)
        self.picking_out.action_confirm()
        self.picking_out.action_assign()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_internal_partially_available(self):
        self.update_stock(self.pp_01, self.stock_loc, 1)
        self.picking_inter.action_confirm()
        self.picking_inter.action_assign()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_inter.id],
            'active_id': self.picking_inter.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
                'location_dest_id': self.transit_inter_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_out_assigned(self):
        self.update_stock(self.pp_01, self.stock_loc, 100)
        self.update_stock(self.pp_02, self.stock_loc, 100)
        self.picking_out.action_confirm()
        self.picking_out.action_assign()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_internal_assigned(self):
        self.update_stock(self.pp_01, self.stock_loc, 100)
        self.update_stock(self.pp_02, self.stock_loc, 100)
        self.picking_inter.action_confirm()
        self.picking_inter.action_assign()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_inter.id],
            'active_id': self.picking_inter.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
                'location_dest_id': self.transit_inter_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_in_assigned(self):
        self.picking_in.action_confirm()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_in.id],
            'active_id': self.picking_in.id}).create({
                'location_dest_id': self.inventory_loss_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_out_done(self):
        self.picking_out.action_confirm()
        self.picking_out.action_done()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_out.id],
            'active_id': self.picking_out.id}).create({
                'location_src_id': self.customer_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_in_done(self):
        self.picking_in.action_confirm()
        self.picking_in.action_done()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_in.id],
            'active_id': self.picking_in.id}).create({
                'location_dest_id': self.inventory_loss_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)

    def test_modify_locations_internal_done(self):
        self.picking_inter.action_confirm()
        self.picking_inter.action_assign()
        self.picking_inter.action_done()
        wiz = self.env['wiz.picking_modify_loc'].with_context({
            'active_model': 'stock.picking',
            'active_ids': [self.picking_inter.id],
            'active_id': self.picking_inter.id}).create({
                'location_src_id': self.inventory_loss_loc_id,
                'location_dest_id': self.transit_inter_loc_id,
            })
        self.assertRaises(Exception, wiz.action_accept)
