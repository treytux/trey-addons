###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from types import SimpleNamespace
from unittest.mock import patch

from odoo import Command
from odoo.addons.portal_account.controllers.portal_account import (
    PortalAccount, PortalAccountCustomerPortal, PortalAccountPortalAccount)
from odoo.tests.common import TransactionCase


class TestPortalAccount(TransactionCase):

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
        })
        self.portal_user = self.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'Portal User',
            'login': 'portal_user_account_test',
            'email': 'portal_user_account_test@example.com',
            'password': 'portal_user_account_test',
            'partner_id': self.contact_partner.id,
            'groups_id': [Command.set([self.group_portal.id])],
        })

    def _request_for_portal_user(self):
        return SimpleNamespace(env=self.env(user=self.portal_user.id))

    def test_get_account_invoice_domain_uses_commercial_partner_id(self):
        controller = PortalAccountCustomerPortal()
        with patch(
            'odoo.addons.portal_account.controllers.portal_account.request',
            self._request_for_portal_user()
        ):
            domain = controller._get_account_invoice_domain()
        self.assertEqual(domain, [
            ('message_partner_ids', 'child_of', [self.company_partner.id]),
            ('state', '=', 'posted'),
        ])

    def test_prepare_portal_layout_values_returns_invoice_count(self):
        controller = PortalAccountPortalAccount()
        domain_mock = [
            ('message_partner_ids', 'child_of', [self.company_partner.id]),
            ('state', '=', 'posted'),
        ]
        controller._get_account_invoice_domain = lambda: domain_mock
        with patch.object(
            PortalAccount, '_prepare_portal_layout_values', return_value={},
        ), patch(
            'odoo.addons.portal_account.controllers.portal_account.request',
            self._request_for_portal_user()
        ), patch.object(
            type(self.env['account.move']), 'search_count', autospec=True,
            return_value=7,
        ) as mocked_search_count, patch.object(
            type(self.env['account.move']),
            'search', autospec=True, return_value=self.env['account.move'],
        ):
            values = controller._prepare_portal_layout_values()
        self.assertEqual(values['invoice_count'], 7)
        self.assertEqual(
            mocked_search_count.call_args.args[1], domain_mock,)

    def test_prepare_portal_layout_values_respects_website_limit_account(self):
        self.website.limit_account = 2
        controller = PortalAccountPortalAccount()
        controller._get_account_invoice_domain = lambda: []
        with patch.object(
            PortalAccount, '_prepare_portal_layout_values', return_value={},
        ), patch(
            'odoo.addons.portal_account.controllers.portal_account.request',
            self._request_for_portal_user()
        ), patch.object(
            type(self.env['account.move']), 'search_count', autospec=True,
            return_value=0,
        ), patch.object(
            type(self.env['account.move']), 'search', autospec=True,
            return_value=self.env['account.move']
        ) as mocked_search:
            controller._prepare_portal_layout_values()
        self.assertEqual(mocked_search.call_args.kwargs['limit'], 2)

    def test_get_and_set_values_manage_website_limit_account(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param('website.limit_account', '9')
        settings = self.env['res.config.settings'].create({
            'website_id': self.website.id,
        })
        values = settings.get_values()
        self.assertEqual(values['limit_account'], 9)
        settings.limit_account = 5
        settings.set_values()
        self.assertEqual(
            config_parameter.get_param('website.limit_account'), '5')
