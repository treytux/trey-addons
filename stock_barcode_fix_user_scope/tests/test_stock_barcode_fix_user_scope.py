###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo.tests.common import TransactionCase, new_test_user


class TestStockBarcodeFixUserScope(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Bus = self.env['bus.bus']

    def _channels_since(self, last_id):
        records = self.Bus.sudo().search([('id', '>', last_id)], order='id asc')
        return [json.loads(record.channel) for record in records]

    def _last_bus_id(self):
        record = self.Bus.sudo().search([], order='id desc', limit=1)
        return record.id if record else 0

    def test_scan_channel_remapped_to_acting_user_partner(self):
        last_id = self._last_bus_id()
        self.Bus._sendone(
            'stock_barcodes_scan', 'actions_barcode', {'apply_inventory': True})
        channels = self._channels_since(last_id)
        dbname = self.env.cr.dbname
        partner = self.env.user.partner_id
        self.assertIn([dbname, 'res.partner', partner.id], channels)
        self.assertNotIn([dbname, 'stock_barcodes_scan'], channels)

    def test_all_barcode_channels_remapped(self):
        last_id = self._last_bus_id()
        self.Bus._sendmany([
            ['stock_barcodes_scan', 'actions_barcode', {}],
            ['stock_barcodes_form_update', 'count_apply_inventory', {}],
            ['stock_barcodes_kanban_update', 'enable_operations', {}],
        ])
        channels = self._channels_since(last_id)
        dbname = self.env.cr.dbname
        partner_channel = [dbname, 'res.partner', self.env.user.partner_id.id]
        self.assertEqual(channels, [partner_channel] * 3)

    def test_message_reaches_acting_user_only(self):
        other = new_test_user(self.env, login='barcode_other_user')
        last_id = self._last_bus_id()
        self.Bus.with_user(other)._sendone(
            'stock_barcodes_scan', 'actions_barcode', {'apply_inventory': True})
        channels = self._channels_since(last_id)
        dbname = self.env.cr.dbname
        self.assertIn(
            [dbname, 'res.partner', other.partner_id.id], channels)
        self.assertNotIn(
            [dbname, 'res.partner', self.env.user.partner_id.id], channels)

    def test_non_barcode_channel_not_affected(self):
        last_id = self._last_bus_id()
        self.Bus._sendone('some_other_channel', 'whatever', {})
        channels = self._channels_since(last_id)
        self.assertIn(
            [self.env.cr.dbname, 'some_other_channel'], channels)

    def test_record_target_not_affected(self):
        last_id = self._last_bus_id()
        channel_partner = self.env.ref('base.partner_admin')
        self.Bus._sendone(channel_partner, 'whatever', {})
        channels = self._channels_since(last_id)
        self.assertIn(
            [self.env.cr.dbname, 'res.partner', channel_partner.id], channels)
