###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from datetime import date

from odoo.tests.common import TransactionCase
from psycopg2.errors import NotNullViolation


class TestComplaintsChannelModels(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')

    def test_01_create_minimal_required_fields(self):
        test_complaint = self.env['complaints.channel'].create({
            'email': 'minimal@test.com',
            'company': self.company.id,
            'people_involved': 'Test Involved',
            'witnesses': 'Test Witness',
            'reportable_facts': 'Test Fact',
            'start_date': date.today(),
            'description': 'Test Description',
        })
        expected_values = {
            'email': 'minimal@test.com',
            'company': self.company.id,
            'people_involved': 'Test Involved',
            'witnesses': 'Test Witness',
            'reportable_facts': 'Test Fact',
            'start_date': date.today(),
            'description': 'Test Description',
        }
        test_complaint = self.env['complaints.channel'].create(expected_values)
        for field, expected in expected_values.items():
            actual = getattr(test_complaint, field)
            if field in ['date_start', 'date_end']:
                self.assertEqual(actual, expected)
            elif field in ['company']:
                self.assertEqual(actual[0].id, expected)
            else:
                self.assertEqual(actual, expected)

    def test_02_create_all_fields(self):
        expected_values = {
            'is_anonymous': True,
            'is_employee': True,
            'name': 'Test',
            'last_name': 'test',
            'email': 'test.test@test.com',
            'phone': '+1234567890',
            'company': self.company.id,
            'work_location': 'Test Office',
            'department': 'Test',
            'people_involved': 'Test Involved',
            'witnesses': 'Test Witness',
            'reportable_facts': 'Test Fact',
            'start_date': date(2025, 3, 25),
            'date_end': date(2025, 3, 26),
            'description': 'Test Description.',
            'evidence_filename': 'test_report.pdf',
            'evidence_file': base64.b64encode(b'test binary data'),
        }
        test_complaint = self.env['complaints.channel'].create(expected_values)
        for field, expected in expected_values.items():
            actual = getattr(test_complaint, field)
            if field in ['date_start', 'date_end']:
                self.assertEqual(actual, expected)
            elif field in ['company']:
                self.assertEqual(actual[0].id, expected)
            else:
                self.assertEqual(actual, expected)
        self.assertEqual(
            base64.b64decode(test_complaint.evidence_file), b'test binary data'
        )
        found = self.env['complaints.channel'].search([
            ('email', '=', 'test.test@test.com'),
        ])
        self.assertEqual(len(found), 1)

    def test_03_required_fields(self):
        required_fields = [
            'email',
            'company',
            'people_involved',
            'witnesses',
            'reportable_facts',
            'start_date',
            'description',
        ]
        base_values = {
            'email': 'minimal@test.com',
            'company': self.company.id,
            'people_involved': 'Test Involved',
            'witnesses': 'Test Witness',
            'reportable_facts': 'Test Fact',
            'start_date': date.today(),
            'description': 'Test Description',
        }
        for field in required_fields:
            vals = base_values.copy()
            vals.pop(field)
            with self.assertRaises(NotNullViolation):
                self.env['complaints.channel'].create(vals)

    def test_4_create_with_end_date_before_start_date(self):
        channel = self.env['complaints.channel'].create({
            'email': 'test@test.com',
            'company': self.company.id,
            'people_involved': 'Test Involved',
            'witnesses': 'Test Witness',
            'reportable_facts': 'Fact',
            'start_date': date(2024, 12, 31),
            'date_end': date(2024, 1, 1),
            'description': 'Desc',
        })
        self.assertEqual(channel.start_date, date(2024, 12, 31))
        self.assertEqual(channel.date_end, date(2024, 1, 1))
