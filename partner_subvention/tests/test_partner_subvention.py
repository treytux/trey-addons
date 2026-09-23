###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestPartnerSubvention(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test partner 1',
        })
        self.partner_02 = self.env['res.partner'].create({
            'name': 'Test partner 2',
        })

    def test_partner_subvention(self):
        form = Form(self.env['partner.subvention'])
        form.name = 'Test subvention'
        form.target = 'Partner subvention.'
        form.dossier_code = 'PS-012345ABC'
        form.entity_subvention_id = self.partner_02
        form.partner_id = self.partner_01
        form.amount_requested = 5000
        subvention = form.save()
        self.assertEqual(subvention.state, 'draft')
        with Form(subvention) as form:
            form.state = 'presented'
            form.save()
        self.assertEqual(subvention.state, 'presented')
        with self.assertRaises(AssertionError) as error:
            with Form(subvention) as form:
                form.name = 'Subvention modified'
                form.save()
        self.assertIn('can\'t write on readonly field', str(error.exception))
        today = datetime.now().date()
        with Form(subvention) as form:
            form.grant_date = today
            form.save()
        self.assertEqual(self.partner_01.get_partner_subvention(), subvention)
        self.assertFalse(self.partner_02.get_partner_subvention())

    def test_constraint_amount_requested(self):
        form = Form(self.env['partner.subvention'])
        form.name = 'Test subvention'
        form.target = 'Partner subvention.'
        form.dossier_code = 'PS-012345ABC'
        form.entity_subvention_id = self.partner_02
        form.partner_id = self.partner_01
        form.amount_requested = 0
        with self.assertRaises(ValidationError) as result:
            subvention = form.save()
        self.assertEqual(
            'The amount requested must be positive.',
            result.exception.args[0])
        form.amount_requested = 100
        subvention = form.save()
        self.assertEqual(subvention.amount_requested, 100)

    def test_constraint_dossier_code_unique(self):
        form = Form(self.env['partner.subvention'])
        form.name = 'Test subvention'
        form.target = 'Partner subvention.'
        form.dossier_code = 'PS-012345ABC'
        form.entity_subvention_id = self.partner_02
        form.partner_id = self.partner_01
        form.amount_requested = 100
        form.save()
        form = Form(self.env['partner.subvention'])
        form.name = 'Test subvention 2'
        form.target = 'Partner subvention.'
        form.dossier_code = 'PS-012345ABC'
        form.entity_subvention_id = self.partner_02
        form.partner_id = self.partner_01
        form.amount_requested = 100
        with self.assertRaises(ValidationError) as result:
            form.save()
        self.assertIn(
            'There is already another partner subvention with this same '
            'dossier code', result.exception.args[0])
