###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import MagicMock, patch

from odoo.addons.website_sale_reference.controllers.website_sale import \
    WebsiteSaleReference
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONTROLLER_REQUEST = (
    'odoo.addons.website_sale_reference.controllers.website_sale.request'
)


@tagged('post_install', '-at_install')
class TestWebsiteSaleReference(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.public_partner')
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
        })
        self.controller = WebsiteSaleReference()

    def _fake_request(self):
        fake_request = MagicMock()
        fake_request.website.sale_get_order.return_value = self.order
        return fake_request

    def test_module_loads(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'website_sale_reference'),
        ])
        self.assertEqual(module.state, 'installed')

    def test_set_client_order_ref_draft_stores_value(self):
        with patch(CONTROLLER_REQUEST, new=self._fake_request()):
            res = self.controller.set_client_order_ref(
                client_order_ref='  REF-001  ')
        self.assertEqual(res, {'client_order_ref': 'REF-001'})
        self.assertEqual(self.order.client_order_ref, 'REF-001')

    def test_set_client_order_ref_empty_clears_value(self):
        self.order.client_order_ref = 'REF-001'
        with patch(CONTROLLER_REQUEST, new=self._fake_request()):
            res = self.controller.set_client_order_ref(client_order_ref='   ')
        self.assertEqual(res, {'client_order_ref': False})
        self.assertFalse(self.order.client_order_ref)

    def test_set_client_order_ref_non_draft_is_ignored(self):
        self.order.state = 'sale'
        with patch(CONTROLLER_REQUEST, new=self._fake_request()):
            res = self.controller.set_client_order_ref(
                client_order_ref='REF-002')
        self.assertEqual(res, {'client_order_ref': False})
        self.assertFalse(self.order.client_order_ref)
