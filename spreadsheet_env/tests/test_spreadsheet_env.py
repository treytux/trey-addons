###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class SpreadsheetEnvTestCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spreadsheet_env = cls.env['spreadsheet.env']

    def test_env_sum_paperformat_margins(self):
        results = self.spreadsheet_env.spreadsheet_env_sum(
            [['report.paperformat', 'margin_top', '[]']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreaterEqual(results[0]['value'], 0)

    def test_env_avg_paperformat_margins(self):
        results = self.spreadsheet_env.spreadsheet_env_avg(
            [['report.paperformat', 'margin_top', '[]']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreaterEqual(results[0]['value'], 0)

    def test_env_count_paperformat(self):
        results = self.spreadsheet_env.spreadsheet_env_count(
            [['report.paperformat', '[]']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreater(results[0]['value'], 0)

    def test_env_sum_with_string_domain(self):
        results = self.spreadsheet_env.spreadsheet_env_sum(
            [['report.paperformat', 'margin_top', "[('name', '=', 'A4')]"]]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreaterEqual(results[0]['value'], 0)

    def test_env_avg_with_domain(self):
        results = self.spreadsheet_env.spreadsheet_env_avg(
            [['report.paperformat', 'margin_top', "[('name', '=', 'A4')]"]]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreaterEqual(results[0]['value'], 0)

    def test_env_sum_invalid_model(self):
        results = self.spreadsheet_env.spreadsheet_env_sum(
            [['invalid.model', 'some_field']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(
            results[0].get('error'),
            'Error should be set for invalid model'
        )
        self.assertEqual(results[0]['value'], 0)

    def test_env_avg_invalid_field(self):
        results = self.spreadsheet_env.spreadsheet_env_avg(
            [['report.paperformat', 'invalid_field_xyz']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(
            results[0].get('error'),
            'Error should be set for invalid field'
        )
        self.assertEqual(results[0]['value'], 0)

    def test_env_sum_non_numeric_field(self):
        results = self.spreadsheet_env.spreadsheet_env_sum(
            [['report.paperformat', 'name']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(
            results[0].get('error'),
            'Error should be set for non-numeric field'
        )
        self.assertEqual(results[0]['value'], 0)

    def test_env_sum_with_list_domain(self):
        results = self.spreadsheet_env.spreadsheet_env_sum(
            [['report.paperformat', 'margin_top', [('name', '=', 'A4')]]]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreaterEqual(results[0]['value'], 0)

    def test_env_count_all_paperformats(self):
        results = self.spreadsheet_env.spreadsheet_env_count(
            [['report.paperformat']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreater(
            results[0]['value'], 0,
            'Paperformat count must be at least 1'
        )

    def test_demo_spreadsheet_created(self):
        model = self.env['spreadsheet.spreadsheet']
        self.assertIsNotNone(model, 'Spreadsheet model must exist')

    def test_env_min_paperformat_margins(self):
        results = self.spreadsheet_env.spreadsheet_env_min(
            [['report.paperformat', 'margin_top']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreaterEqual(results[0]['value'], 0)

    def test_env_max_paperformat_margins(self):
        results = self.spreadsheet_env.spreadsheet_env_max(
            [['report.paperformat', 'margin_top']]
        )
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].get('error'))
        self.assertGreaterEqual(results[0]['value'], 0)

    def test_env_sum_batch_multiple(self):
        results = self.spreadsheet_env.spreadsheet_env_sum([
            ['report.paperformat', 'margin_top', '[]'],
            ['report.paperformat', 'margin_top', "[('name', '=', 'A4')]"],
        ])
        self.assertEqual(len(results), 2)
        self.assertIsNone(results[0].get('error'))
        self.assertIsNone(results[1].get('error'))
