###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockPickingSignerApp(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test company',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.serial = 'testingdeviceserial'
        self.passphrase = 'password'
        self.device = self.env['iot.device'].create({
            'name': 'Device',
        })
        self.device_input = self.env['iot.device.input'].create({
            'name': 'Input',
            'device_id': self.device.id,
            'active': True,
            'serial': self.serial,
            'passphrase': self.passphrase,
            'call_model_id': self.ref('stock.model_stock_picking'),
            'call_function': 'sign_stock_picking',
        })
        self.iot = self.env['iot.device.input']
        self.location = self.env.ref('stock.stock_location_stock')

    def test_sign_stock_picking(self):
        self.env.user.signed_device = self.device
        iot = self.iot.get_device(
            serial=self.serial, passphrase=self.passphrase)
        self.assertEqual(iot, self.device_input)
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'location_id': self.location.id,
        })
        inventory._action_done()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        picking.button_signed()
        self.assertEqual(
            self.env.user.signed_device.id,
            picking.signature_device.id)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        signature = 'signature.pdf'
        photo = 'photo.pdf'
        data = {
            'signature': signature,
            'photo': photo,
        }
        res = self.device_input.call_device(data)
        self.assertEqual(res, {'status': 'ok', 'value': data})
        self.assertTrue(self.device_input.action_ids)
        self.assertEqual(self.device_input.action_ids.args, str(data))
        self.assertEqual(self.device_input.action_ids.res, str(res))
        self.assertEqual(len(picking.signature_device), 0)
