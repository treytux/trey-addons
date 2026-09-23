###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json

from odoo.tests.common import HttpCase, tagged

PNG_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P'
    '+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=='
)


@tagged('post_install', '-at_install')
class TestDeliveryProof(HttpCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Proof partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Proof product',
            'list_price': 30,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 5,
                }),
            ],
        })
        self.sale.action_confirm()
        self.picking = self.sale.picking_ids[0]
        self.picking.action_confirm()
        self.picking.action_assign()
        for move in self.picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        self.picking._action_done()
        self.picking.pending_signed = 'pending'
        self.token = self.picking._portal_ensure_token()

    def _accept_photo(self, params):
        payload = {'jsonrpc': '2.0', 'method': 'call', 'params': params}
        response = self.url_open(
            '/my/pending_picking/%s/accept_photo' % self.picking.id,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        return response.json().get('result')

    def _store_photo(self):
        return self._accept_photo({
            'access_token': self.token,
            'name': 'Warehouse operator',
            'filename': 'albaran_sellado.png',
            'image': 'data:image/png;base64,%s' % PNG_B64,
        })

    def test_accept_photo_stores_full_resolution_and_attachment(self):
        result = self._store_photo()
        self.assertTrue(result.get('force_refresh'))
        self.picking.invalidate_recordset()
        self.assertTrue(self.picking.delivery_proof_image)
        self.assertEqual(
            base64.b64decode(self.picking.delivery_proof_image),
            base64.b64decode(PNG_B64))
        self.assertEqual(
            self.picking.delivery_proof_filename, 'albaran_sellado.png')
        self.assertEqual(
            self.picking.delivery_proof_attachment_id.datas,
            self.picking.delivery_proof_image)
        self.assertEqual(self.picking.pending_signed, 'signed')
        self.assertEqual(self.picking.signed_by, 'Warehouse operator')
        self.assertTrue(self.picking.is_signed)
        attachment = self.picking.delivery_proof_attachment_id
        self.assertTrue(attachment)
        self.assertEqual(attachment.res_model, 'stock.picking')
        self.assertEqual(attachment.res_id, self.picking.id)

    def test_accept_photo_requires_token(self):
        result = self._accept_photo({
            'access_token': 'wrong-token',
            'image': 'data:image/png;base64,%s' % PNG_B64,
        })
        self.assertEqual(result.get('error'), 'Invalid order')
        self.picking.invalidate_recordset()
        self.assertFalse(self.picking.delivery_proof_image)

    def test_accept_photo_missing_image(self):
        result = self._accept_photo({
            'access_token': self.token,
            'image': '',
        })
        self.assertEqual(result.get('error'), 'Photo is missing.')

    def test_delivery_proof_requires_login(self):
        self._store_photo()
        response = self.url_open(
            '/picking/%s/delivery_proof' % self.picking.id,
            allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn('/web/login', response.headers.get('Location', ''))

    def test_delivery_proof_internal_user_ok(self):
        self._store_photo()
        self.authenticate('admin', 'admin')
        response = self.url_open(
            '/picking/%s/delivery_proof' % self.picking.id)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.headers.get('Content-Type', '').startswith('image/'))
        self.assertEqual(response.content, base64.b64decode(PNG_B64))

    def test_delivery_proof_portal_user_forbidden(self):
        self._store_photo()
        portal_user = self.env['res.users'].create({
            'name': 'Portal user',
            'login': 'proof_portal_user',
            'password': 'proof_portal_user',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.authenticate(portal_user.login, 'proof_portal_user')
        response = self.url_open(
            '/picking/%s/delivery_proof' % self.picking.id,
            allow_redirects=False)
        self.assertEqual(response.status_code, 403)

    def test_delivery_proof_not_found_without_photo(self):
        self.authenticate('admin', 'admin')
        response = self.url_open(
            '/picking/%s/delivery_proof' % self.picking.id,
            allow_redirects=False)
        self.assertEqual(response.status_code, 404)
