###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestResPartnerBank(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner',
        })
        self.user_without_permission = self.env['res.users'].create({
            'login': 'user_without_permission',
            'name': 'User without permission',
            'email': 'user_without_permission@test.es',
            'groups_id': [
                (4, self.env.ref('base.group_user').id),
            ]
        })
        self.user_with_permission = self.env['res.users'].create({
            'login': 'user_with_permission',
            'name': 'User with permission',
            'email': 'user_with_permission@test.es',
            'groups_id': [
                (4, self.env.ref('base.group_user').id),
                (4, self.env.ref('base.group_partner_manager').id),
            ]
        })
        templates = self.env['account.chart.template'].search([])
        if not templates:
            _log.warn(
                'Test skipped because there is no chart of account defined.')
            self.skipTest('No account chart template found.')
            return

    def test_user_without_permission(self):
        with self.assertRaises(AccessError):
            self.env['res.partner.bank'].sudo(
                self.user_without_permission).create({
                    'acc_type': 'bank',
                    'company_id': self.env.user.company_id.id,
                    'partner_id': self.partner.id,
                    'acc_number': '123456789',
                    'bank_id': self.ref('base.res_bank_1'),
                })

    def test_user_with_permission(self):
        self.env['res.partner.bank'].sudo(
            self.user_with_permission).create({
                'acc_type': 'bank',
                'company_id': self.env.user.company_id.id,
                'partner_id': self.partner.id,
                'acc_number': '123456789',
                'bank_id': self.ref('base.res_bank_1'),
            })
