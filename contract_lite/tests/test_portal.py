# Copyright 2026 Trey - Kilobytes de Soluciones
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import odoo.tests
from odoo import http

from .common import ContractLiteTestCommonMixin


@odoo.tests.tagged('post_install', '-at_install')
class TestContractLitePortal(ContractLiteTestCommonMixin, odoo.tests.HttpCase):
    def setUp(self):
        super().setUp()
        self.portal_login = 'portal_contract_lite'
        self.portal_password = 'portal_contract_lite'
        self.user_portal = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Portal Contract Lite User',
                'login': self.portal_login,
                'email': 'portal_contract_lite@example.com',
                'password': self.portal_password,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
            })
        self.other_partner = self.env['res.partner'].create({
            'name': 'Other Portal Partner',
            'customer_rank': 1,
        })
        self.product = self._get_test_product()
        self.contract = self.env['contract_lite.contract'].create({
            'name': 'Portal Contract Lite',
            'partner_id': self.user_portal.partner_id.id,
            'state': 'active',
        })
        self._create_contract_line(
            self.contract,
            self.product,
            date_start='2026-01-01',
            recurring_next_date='2026-01-01',
            automatic_price=False,
            price_unit=10.0,
        )
        self.other_contract = self.env['contract_lite.contract'].create({
            'name': 'Not Visible Contract Lite',
            'partner_id': self.other_partner.id,
            'state': 'active',
        })
        self._create_contract_line(
            self.other_contract,
            self.product,
            date_start='2026-01-01',
            recurring_next_date='2026-01-01',
            automatic_price=False,
            price_unit=10.0,
        )
        self.contract._portal_ensure_token()
        self.other_contract._portal_ensure_token()

    def test_portal_list_and_detail(self):
        self.authenticate(self.portal_login, self.portal_password)
        http.root.session_store.save(self.session)
        response = self.url_open('/my/contracts-lite')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.contract.name, response.text)
        self.assertNotIn(self.other_contract.name, response.text)
        detail_url = '/my/contracts-lite/{}?access_token={}'.format(
            self.contract.id,
            self.contract.access_token
        )
        detail_response = self.url_open(detail_url)
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn(self.contract.name, detail_response.text)

    def test_forbidden_contract_redirects(self):
        self.authenticate(self.portal_login, self.portal_password)
        http.root.session_store.save(self.session)
        forbidden_url = '/my/contracts-lite/{}?access_token={}'.format(
            self.other_contract.id,
            self.other_contract.access_token
        )
        response = self.url_open(forbidden_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my', response.url)

    def test_contract_detail_without_token_redirects(self):
        self.authenticate(self.portal_login, self.portal_password)
        http.root.session_store.save(self.session)
        detail_url = '/my/contracts-lite/{}'.format(self.other_contract.id)
        response = self.url_open(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my', response.url)

    def test_portal_list_sorting_by_name(self):
        self.authenticate(self.portal_login, self.portal_password)
        http.root.session_store.save(self.session)
        self.env['contract_lite.contract'].create({
            'name': 'AAA Contract Lite',
            'partner_id': self.user_portal.partner_id.id,
            'state': 'active',
        })
        response = self.url_open('/my/contracts-lite?sortby=name')
        self.assertEqual(response.status_code, 200)
        self.assertIn('AAA Contract Lite', response.text)
