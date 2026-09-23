import re

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('stock_picking_return_address', 'post_install', '-at_install')
class TestStockPickingReturnAddress(TransactionCase):

    def setUp(self):
        super().setUp()
        self.report_model = self.env['ir.actions.report']
        self.partner_model = self.env['res.partner']
        self.picking_model = self.env['stock.picking']
        self.stock_location_stock = self.env.ref('stock.stock_location_stock')
        self.stock_location_customers = self.env.ref(
            'stock.stock_location_customers'
        )
        self.stock_location_suppliers = self.env.ref(
            'stock.stock_location_suppliers'
        )
        warehouse = self.env.ref('stock.warehouse0')
        self.picking_type_in = warehouse.in_type_id
        self.picking_type_out = warehouse.out_type_id
        self.product = self.env['product.product'].create({
            'name': 'Test Product Picking Address',
            'type': 'consu',
        })

    def _render_deliveryslip_html(self, picking):
        result = self.report_model._render_qweb_html(
            'stock.report_deliveryslip', picking.ids, False
        )
        html = result[0]
        return html.decode() if isinstance(html, bytes) else str(html)

    def _create_partner(self, vals):
        return self.partner_model.create(vals)

    def _get_picking_locations(self, picking_type):
        location_id = picking_type.default_location_src_id
        location_dest_id = picking_type.default_location_dest_id
        if not location_id:
            if picking_type.code == 'incoming':
                location_id = self.stock_location_suppliers
            else:
                location_id = self.stock_location_stock
        if not location_dest_id:
            if picking_type.code == 'outgoing':
                location_dest_id = self.stock_location_customers
            else:
                location_dest_id = self.stock_location_stock
        return location_id, location_dest_id

    def _create_picking(self, picking_type, partner):
        location_id, location_dest_id = self._get_picking_locations(
            picking_type
        )
        return self.picking_model.create({
            'partner_id': partner.id,
            'picking_type_id': picking_type.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'company_id': picking_type.company_id.id,
            'move_ids': [
                (0, 0, {
                    'name': self.product.display_name,
                    'product_id': self.product.id,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1.0,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                }),
            ],
        })

    def _mark_picking_as_return(self, picking, partner):
        source_picking = self._create_picking(self.picking_type_out, partner)
        source_move = source_picking.move_ids[:1]
        self.assertTrue(source_move)
        picking.move_ids.write({'origin_returned_move_id': source_move.id})

    def test_report_does_not_show_picking_address_for_regular_incoming(self):
        partner = self._create_partner({
            'name': 'Partner Return',
            'street': 'Calle Falsa 123',
            'zip': '28001',
            'city': 'Madrid',
            'phone': '600123123',
        })
        picking = self._create_picking(self.picking_type_in, partner)
        html = self._render_deliveryslip_html(picking)
        self.assertIn('name="vendor_address"', html)
        self.assertNotIn('name="picking_address"', html)
        self.assertIn('Calle Falsa 123', html)
        self.assertIn('600123123', html)

    def test_report_shows_picking_address_for_incoming_return(self):
        partner = self._create_partner({
            'name': 'Partner Return',
            'street': 'Calle Falsa 123',
            'zip': '28001',
            'city': 'Madrid',
            'phone': '600123123',
        })
        picking = self._create_picking(self.picking_type_in, partner)
        self._mark_picking_as_return(picking, partner)
        html = self._render_deliveryslip_html(picking)
        self.assertNotIn('name="vendor_address"', html)
        self.assertIn('name="picking_address"', html)
        self.assertIn('600123123', html)

    def test_report_does_not_show_picking_address_for_outgoing(self):
        partner = self._create_partner({'name': 'Partner Outgoing'})
        picking = self._create_picking(self.picking_type_out, partner)
        html = self._render_deliveryslip_html(picking)
        self.assertNotIn('name="vendor_address"', html)
        self.assertNotIn('name="picking_address"', html)

    def test_report_uses_partner_contact_address(self):
        company_partner = self._create_partner({
            'name': 'Parent Company',
            'street': 'Avenida Empresa 1',
            'zip': '28002',
            'city': 'Madrid',
            'phone': '911111111',
        })
        contact_partner = self._create_partner({
            'name': 'Child Contact',
            'type': 'delivery',
            'parent_id': company_partner.id,
            'street': 'Calle Contacto 99',
            'zip': '28003',
            'city': 'Madrid',
            'phone': '600999999',
        })
        picking = self._create_picking(self.picking_type_in, contact_partner)
        self._mark_picking_as_return(picking, contact_partner)
        html = self._render_deliveryslip_html(picking)
        self.assertNotIn('name="vendor_address"', html)
        self.assertIn('name="picking_address"', html)
        self.assertIn('600999999', html)
        self.assertNotIn('911111111', html)

    def test_report_shows_picking_address_in_information_block_column(self):
        partner = self._create_partner({'name': 'Partner Incoming'})
        picking = self._create_picking(self.picking_type_in, partner)
        self._mark_picking_as_return(picking, partner)
        html = self._render_deliveryslip_html(picking)
        pattern = re.compile(
            r'<div name="information_block" class="col-6">.*?'
            r'name="picking_address".*?</div>\s*'
            r'<div name="address" class="col-5 offset-1">',
            re.S,
        )
        self.assertRegex(html, pattern)

    def test_report_does_not_show_customer_address_block_for_incoming(self):
        partner = self._create_partner({'name': 'Partner Incoming'})
        picking = self._create_picking(self.picking_type_in, partner)
        html = self._render_deliveryslip_html(picking)
        self.assertNotIn('name="customer_address"', html)
