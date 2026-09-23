###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from urllib.parse import urlparse

import odoo.tests
from odoo import Command, fields, http


@odoo.tests.tagged('post_install', '-at_install')
class TestPortalPurchase(odoo.tests.HttpCase):

    def setUp(self):
        super().setUp()
        self.portal_login = 'portal_purchase_user'
        self.portal_password = 'portal_purchase_user'
        self.invoice_number = 'FAC-2026-0001'
        self.invoice_date = '2026-04-16'
        self.invoice_file_content = b'portal purchase invoice content'
        self.portal_user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Portal Purchase User',
                'login': self.portal_login,
                'email': 'portal_purchase_user@example.com',
                'password': self.portal_password,
                'partner_id': self.env['res.partner'].create({
                    'name': 'Portal Purchase Partner',
                    'email': 'portal_purchase_user@example.com',
                }).id,
                'groups_id': [Command.set([self.env.ref('base.group_portal').id])],
            })
        self.other_partner = self.env['res.partner'].create({
            'name': 'Other Purchase Partner',
            'email': 'other_purchase_partner@example.com',
        })
        self.product = self.env['product.product'].create({
            'name': 'Portal Purchase Product',
            'detailed_type': 'consu',
            'purchase_ok': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.portal_purchase_order = self._create_purchase_order(
            self.portal_user.partner_id)
        self.other_purchase_order = self._create_purchase_order(
            self.other_partner)

    def _authenticate_portal_user(self):
        self.authenticate(self.portal_login, self.portal_password)
        http.root.session_store.save(self.session)

    def _create_purchase_order(self, partner):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'order_line': [Command.create({
                'name': self.product.name,
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 50.0,
                'date_planned': fields.Datetime.now(),
                'product_uom': self.product.uom_po_id.id,
            })],
        })
        purchase_order.button_confirm()
        purchase_order._portal_ensure_token()
        return purchase_order

    def _upload_invoice(self, purchase_order, allow_redirects=True):
        return self.url_open(
            '/my/upload_purchase_invoice/%s' % purchase_order.id,
            data={
                'csrf_token': http.Request.csrf_token(self),
                'supplier_invoice_number': self.invoice_number,
                'supplier_invoice_date': self.invoice_date,
            },
            files={
                'supplier_invoice_file': (
                    'supplier_invoice.pdf',
                    self.invoice_file_content,
                    'application/pdf',
                ),
            },
            allow_redirects=allow_redirects)

    def _assert_redirect_path(self, response, expected_path):
        location = response.headers.get('Location')
        self.assertTrue(location)
        if location.startswith('http'):
            self.assertEqual(urlparse(location).path, expected_path)
        else:
            self.assertEqual(location, expected_path)

    def test_unauthorized_access_redirects_to_purchase_detail(self):
        self._authenticate_portal_user()
        response = self._upload_invoice(
            self.other_purchase_order, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self._assert_redirect_path(
            response, '/my/purchase/%s' % self.other_purchase_order.id)
        self.other_purchase_order.invalidate_recordset()
        self.assertFalse(self.other_purchase_order.supplier_invoice_number)
        self.assertFalse(self.other_purchase_order.supplier_invoice_date)
        self.assertFalse(self.other_purchase_order.supplier_invoice_file)

    def test_valid_submission_stores_supplier_invoice_fields(self):
        self._authenticate_portal_user()
        self._upload_invoice(self.portal_purchase_order)
        self.portal_purchase_order.invalidate_recordset()
        self.assertEqual(
            self.portal_purchase_order.supplier_invoice_number,
            self.invoice_number)
        self.assertEqual(
            self.portal_purchase_order.supplier_invoice_date,
            fields.Date.from_string(self.invoice_date))
        self.assertEqual(
            base64.b64decode(self.portal_purchase_order.supplier_invoice_file),
            self.invoice_file_content)

    def test_submission_redirects_to_purchase_detail(self):
        self._authenticate_portal_user()
        response = self._upload_invoice(
            self.portal_purchase_order, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self._assert_redirect_path(
            response, '/my/purchase/%s' % self.portal_purchase_order.id)

    def test_detail_template_shows_invoice_data_instead_of_form(self):
        self.portal_purchase_order.write({
            'supplier_invoice_number': 'INV-PORTAL-42',
            'supplier_invoice_date': fields.Date.from_string('2026-04-16'),
            'supplier_invoice_file': base64.b64encode(b'fake invoice'),
        })
        self._authenticate_portal_user()
        response = self.url_open(
            '/my/purchase/%s' % self.portal_purchase_order.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('INV-PORTAL-42', response.text)
        self.assertIn('Download invoice', response.text)
        self.assertIn(
            '/web/content/?model=purchase.order&amp;id=%s'
            % self.portal_purchase_order.id, response.text)
        self.assertNotIn('o_pp_invoice_upload_form', response.text)
