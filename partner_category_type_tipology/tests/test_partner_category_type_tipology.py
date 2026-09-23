###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPartnerCategoryTypeTipology(TransactionCase):

    def test_create_valid_partner_typology(self):
        category = self.env['res.partner.category'].create({
            'name': 'Test Typology',
            'is_partner_typology': True,
            'min_planned_rate': 0.75,
            'max_planned_rate': 0.90,
        })
        self.assertTrue(category.is_partner_typology)

    def test_partner_typology_rates_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            self.env['res.partner.category'].create({
                'name': 'Negative Typology',
                'is_partner_typology': True,
                'min_planned_rate': -0.10,
                'max_planned_rate': 0.90,
            })

    def test_partner_typology_min_rate_cannot_exceed_max_rate(self):
        with self.assertRaises(ValidationError):
            self.env['res.partner.category'].create({
                'name': 'Invalid Typology',
                'is_partner_typology': True,
                'min_planned_rate': 0.95,
                'max_planned_rate': 0.90,
            })

    def test_non_typology_category_allows_default_rates(self):
        category = self.env['res.partner.category'].create({
            'name': 'Regular Category',
        })
        self.assertFalse(category.is_partner_typology)

    def test_assign_partner_typology_and_related_rates(self):
        category = self.env['res.partner.category'].create({
            'name': 'Related Rates Typology',
            'is_partner_typology': True,
            'min_planned_rate': 0.60,
            'max_planned_rate': 0.80,
        })
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'partner_typology_id': category.id,
        })
        self.assertEqual(partner.partner_typology_id, category)
        self.assertEqual(
            partner.partner_typology_min_planned_rate,
            category.min_planned_rate)
        self.assertEqual(
            partner.partner_typology_max_planned_rate,
            category.max_planned_rate)

    def test_initial_partner_typology_categories(self):
        xml_ids = [
            'partner_category_type_tipology.res_partner_category_typology_a',
            'partner_category_type_tipology.res_partner_category_typology_b',
            'partner_category_type_tipology.res_partner_category_typology_c',
            'partner_category_type_tipology.res_partner_category_typology_d',
        ]
        categories = self.env['res.partner.category'].browse([
            self.env.ref(xml_id).id for xml_id in xml_ids
        ])
        expected_names = [
            'A - Strategic',
            'B - Relevant',
            'C - Standard',
            'D - Reactive',
        ]
        self.assertEqual(len(categories), 4)
        self.assertTrue(all(categories.mapped('is_partner_typology')))
        self.assertEqual(categories.mapped('name'), expected_names)
