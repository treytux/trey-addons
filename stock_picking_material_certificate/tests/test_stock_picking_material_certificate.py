###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockPickingMaterialCertificate(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self._create_record(
            model_name='res.partner',
            vals={
                'name': 'Test partner',
                'is_company': True,
            }
        )
        self.product = self._create_record(
            model_name='product.product',
            vals={
                'type': 'product',
                'company_id': False,
                'name': 'Test product 1',
                'standard_price': 10,
                'list_price': 30,
                'tracking': 'lot',
            }
        )

    def _create_record(self, model_name, vals):
        record = self._create_vals(model_name, vals)
        return record.create(record._convert_to_write(record._cache))

    def _create_vals(self, model_name, vals):
        model = self.env[model_name]
        data = model.default_get(list(model.fields_get()))
        data.update(vals)
        return model.new(data)

    def test_picking_in(self):
        location_stock = self.env.ref('stock.stock_location_stock')
        location_supplier = self.env.ref('stock.stock_location_suppliers')
        picking = self._create_record('stock.picking', {
            'partner_id': self.partner.id,
            'location_id': location_supplier.id,
            'location_dest_id': location_stock.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        lot = self._create_record(model_name='stock.production.lot', vals={
            'name': 'Test lot',
            'certificate_number': 'LOT NUMBER',
            'product_id': self.product.id,
        })
        self.assertEqual(len(picking.move_lines), 1)
        move = picking.move_lines
        move.quantity_done = move.product_uom_qty
        self.assertEqual(len(move.move_line_ids), 1)
        move_line = move.move_line_ids[0]
        self.assertNotEqual(move.has_tracking, 'none')
        picking_type = move.picking_type_id or move.picking_id.picking_type_id
        self.assertTrue(
            picking_type.use_existing_lots or picking_type.use_create_lots)
        move_line.lot_id = lot.id
        move_line.onchange_serial_number()
        self.assertEqual(move_line.certificate_number, 'LOT NUMBER')
        lot.certificate_number = False
        move_line.lot_id = lot.id
        move_line.onchange_serial_number()
        self.assertEqual(move_line.certificate_number, 'LOT NUMBER')
        move_line.certificate_number = 'MOVE NUMBER'
        picking.action_done()
        self.assertEqual(lot.certificate_number, 'MOVE NUMBER')
