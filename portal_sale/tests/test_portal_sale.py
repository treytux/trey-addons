###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from types import SimpleNamespace
from unittest.mock import patch

from odoo import Command
from odoo.addons.portal_sale.controllers.portal_sale import (
    PortalSale, PortalSaleCustomerPortal, PortalSalePortalSale)
from odoo.tests.common import TransactionCase


class TestPortalSale(TransactionCase):

    def setUp(self):
        super().setUp()
        self.group_portal = self.env.ref('base.group_portal')
        self.website = self.env['website'].get_current_website()
        self.company_partner = self.env['res.partner'].create({
            'name': 'Commercial Partner',
        })
        self.contact_partner = self.env['res.partner'].create({
            'name': 'Portal Contact',
            'parent_id': self.company_partner.id,
            'email': 'portal_sale_contact@example.com',
        })
        self.portal_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Portal User',
            'login': 'portal_user_sale_test',
            'email': 'portal_user_sale_test@example.com',
            'password': 'portal_user_sale_test',
            'partner_id': self.contact_partner.id,
            'groups_id': [Command.set([self.group_portal.id])],
        })
        self.other_partner = self.env['res.partner'].create({
            'name': 'Other Partner',
            'email': 'other_partner_sale_test@example.com',
        })
        self.sale_orders = self.env['sale.order'].sudo().create([
            {
                'partner_id': self.contact_partner.id,
                'state': 'sent',
                'name': 'SO-TEST-SENT-1',
                'date_order': '2024-01-10 10:00:00',
                'message_partner_ids': [Command.link(self.company_partner.id)],
            },
            {
                'partner_id': self.contact_partner.id,
                'state': 'sent',
                'name': 'SO-TEST-SENT-2',
                'date_order': '2024-01-11 10:00:00',
                'message_partner_ids': [Command.link(self.company_partner.id)],
            },
            {
                'partner_id': self.contact_partner.id,
                'state': 'sale',
                'name': 'SO-TEST-SALE',
                'date_order': '2024-01-12 10:00:00',
                'message_partner_ids': [Command.link(self.company_partner.id)],
            },
            {
                'partner_id': self.contact_partner.id,
                'state': 'done',
                'name': 'SO-TEST-DONE',
                'date_order': '2024-01-13 10:00:00',
                'message_partner_ids': [Command.link(self.company_partner.id)],
            },
            {
                'partner_id': self.other_partner.id,
                'state': 'sent',
                'name': 'SO-OTHER-SENT',
                'date_order': '2024-01-14 10:00:00',
                'message_partner_ids': [Command.link(self.other_partner.id)],
            },
        ])

    def _request_for_portal_user(self, context=None):
        return SimpleNamespace(
            env=self.env(user=self.portal_user.id),
            context=context or {})

    def test_get_sale_quotation_domain_uses_commercial_partner_and_sent(self):
        controller = PortalSaleCustomerPortal()
        with patch(
            'odoo.addons.portal_sale.controllers.portal_sale.request',
            self._request_for_portal_user()
        ):
            domain = controller._get_sale_quotation_domain()
        self.assertEqual(domain, [
            ('message_partner_ids', 'child_of', [self.company_partner.id]),
            ('state', '=', 'sent'),
        ])

    def test_get_sale_order_domain_uses_commercial_partner_and_sale_done(self):
        controller = PortalSaleCustomerPortal()
        with patch(
            'odoo.addons.portal_sale.controllers.portal_sale.request',
            self._request_for_portal_user()
        ):
            domain = controller._get_sale_order_domain()
        self.assertEqual(domain, [
            ('message_partner_ids', 'child_of', [self.company_partner.id]),
            ('state', 'in', ['sale', 'done']),
        ])

    def test_portal_layout_counts_limit(self):
        self.website.limit_orders_quotations = 1
        controller = PortalSalePortalSale()
        controller._get_sale_order_domain = lambda: [
            ('message_partner_ids', 'child_of', [self.company_partner.id]),
            ('state', 'in', ['sale', 'done']),
        ]
        controller._get_sale_quotation_domain = lambda: [
            ('message_partner_ids', 'child_of', [self.company_partner.id]),
            ('state', '=', 'sent'),
        ]
        with patch.object(
            PortalSale, '_prepare_portal_layout_values', return_value={
                'base': True,
            }
        ), patch(
            'odoo.addons.portal_sale.controllers.portal_sale.request',
            self._request_for_portal_user()
        ):
            values = controller._prepare_portal_layout_values()
        self.assertTrue(values['base'])
        self.assertEqual(values['quotation_count'], 2)
        self.assertEqual(values['order_count'], 2)
        self.assertEqual(len(values['quotation_sent']), 1)
        self.assertEqual(len(values['orders_sale_done']), 1)
        self.assertEqual(values['quotation_sent'].state, 'sent')
        self.assertIn(values['orders_sale_done'].state, ['sale', 'done'])

    def test_portal_my_quotes_sets_domain_request_in_context(self):
        controller = PortalSalePortalSale()
        fake_request = self._request_for_portal_user(context={'lang': 'es_ES'})
        with patch(
            'odoo.addons.portal_sale.controllers.portal_sale.request',
            fake_request
        ), patch.object(
            PortalSale, 'portal_my_quotes', autospec=True,
            return_value='quotes_result'
        ) as mocked_super:
            result = controller.portal_my_quotes.__wrapped__(
                controller, page=2, sortby='date')
        self.assertEqual(result, 'quotes_result')
        self.assertEqual(
            fake_request.update_context['domain_request'], 'portal_my_quotes')
        self.assertEqual(fake_request.update_context['lang'], 'es_ES')
        self.assertEqual(mocked_super.call_args.kwargs['page'], 2)
        self.assertEqual(mocked_super.call_args.kwargs['sortby'], 'date')

    def test_portal_my_orders_sets_domain_request_in_context(self):
        controller = PortalSalePortalSale()
        fake_request = self._request_for_portal_user(context={'tz': 'UTC'})
        with patch(
            'odoo.addons.portal_sale.controllers.portal_sale.request',
            fake_request
        ), patch.object(
            PortalSale, 'portal_my_orders', autospec=True,
            return_value='orders_result'
        ) as mocked_super:
            result = controller.portal_my_orders.__wrapped__(
                controller, page=3, sortby='name')
        self.assertEqual(result, 'orders_result')
        self.assertEqual(
            fake_request.update_context['domain_request'], 'portal_my_orders')
        self.assertEqual(fake_request.update_context['tz'], 'UTC')
        self.assertEqual(mocked_super.call_args.kwargs['page'], 3)
        self.assertEqual(mocked_super.call_args.kwargs['sortby'], 'name')

    def test_get_and_set_values_manage_website_limit_orders_quotations(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param('website.limit_orders_quotations', '9')
        settings = self.env['res.config.settings'].create({
            'website_id': self.website.id,
        })
        values = settings.get_values()
        self.assertEqual(values['limit_orders_quotations'], 9)
        settings.limit_orders_quotations = 5
        settings.set_values()
        self.assertEqual(
            config_parameter.get_param('website.limit_orders_quotations'), '5')
