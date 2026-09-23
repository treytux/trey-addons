###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import MagicMock, patch

from odoo.addons.website_sale_observations.controllers.website_sale import \
    WebsiteSaleObservations
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONTROLLER_REQUEST = (
    'odoo.addons.website_sale_observations.controllers.website_sale.request'
)


@tagged('post_install', '-at_install')
class TestWebsiteSaleObservations(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.public_partner')
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
        })
        self.controller = WebsiteSaleObservations()

    def _fake_request(self):
        fake_request = MagicMock()
        fake_request.website.sale_get_order.return_value = self.order
        return fake_request

    def test_module_loads(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'website_sale_observations'),
        ])
        self.assertEqual(module.state, 'installed')

    def test_field_is_available(self):
        self.assertIn(
            'web_order_observations', self.env['sale.order']._fields)

    def test_set_observations_draft_stores_value(self):
        with patch(CONTROLLER_REQUEST, new=self._fake_request()):
            res = self.controller.set_web_order_observations(
                observations='  Deliver in the morning  ')
        self.assertEqual(res, {'observations': 'Deliver in the morning'})
        self.assertEqual(
            self.order.web_order_observations, 'Deliver in the morning')

    def test_set_observations_empty_clears_value(self):
        self.order.web_order_observations = 'Some note'
        with patch(CONTROLLER_REQUEST, new=self._fake_request()):
            res = self.controller.set_web_order_observations(
                observations='   ')
        self.assertEqual(res, {'observations': False})
        self.assertFalse(self.order.web_order_observations)

    def test_set_observations_non_draft_is_ignored(self):
        self.order.state = 'sale'
        with patch(CONTROLLER_REQUEST, new=self._fake_request()):
            res = self.controller.set_web_order_observations(
                observations='Late note')
        self.assertEqual(res, {'observations': False})
        self.assertFalse(self.order.web_order_observations)
