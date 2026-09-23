###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
from datetime import datetime
from unittest.mock import patch

import pandas as pd
from odoo.exceptions import UserError
from odoo.tests import common


class TestImportTemplate(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.import_template_model = self.env['import.template']
        self.import_file_model = self.env['import.file']
        self.template = self.import_template_model.create({
            'name': 'Test template',
            'description': '<p>Template for tests</p>',
        })
        model = self.env['ir.model'].search([
            ('model', '=', 'import.file.line'),
        ], limit=1)
        self.template_with_model = self.import_template_model.create({
            'name': 'Test template with model',
            'description': '<p>Template for flow tests</p>',
            'model_id': model.id,
        })

    def _create_wizard(self, filename, raw_bytes, template=None, simulate=True):
        return self.import_file_model.create({
            'template_id': (template or self.template).id,
            'file_filename': filename,
            'file': base64.b64encode(raw_bytes),
            'simulate': simulate,
        })

    def test_dataframe_get_csv(self):
        wizard = self._create_wizard('partners.csv', b'name,qty\nA,1\nB,2\n')
        df = wizard.dataframe_get()
        self.assertEqual(list(df.columns), ['name', 'qty'])
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['name'], 'A')
        self.assertEqual(df.iloc[1]['qty'], 2)

    def test_dataframe_get_txt(self):
        wizard = self._create_wizard('partners.txt', b'name\tqty\nA\t1\nB\t2\n')
        df = wizard.dataframe_get()
        self.assertEqual(list(df.columns), ['name', 'qty'])
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['name'], 'A')
        self.assertEqual(df.iloc[1]['qty'], 2)

    def test_dataframe_get_xlsx(self):
        buf = io.BytesIO()
        pd.DataFrame([{'name': 'A', 'qty': 1}]).to_excel(buf, index=False)
        wizard = self._create_wizard('partners.xlsx', buf.getvalue())
        df = wizard.dataframe_get()
        self.assertEqual(list(df.columns), ['name', 'qty'])
        self.assertEqual(df.iloc[0]['name'], 'A')
        self.assertEqual(df.iloc[0]['qty'], 1)

    def test_dataframe_get_invalid_extension(self):
        wizard = self._create_wizard('partners.json', b'{"name": "A"}')
        with self.assertRaisesRegex(UserError, 'File extension must be'):
            wizard.dataframe_get()

    def test_dataframe_required_columns_missing(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        df = pd.DataFrame([{'name': 'A'}])
        with self.assertRaisesRegex(UserError, 'Missing columns in file'):
            wizard.dataframe_required_columns(df, ['name', 'qty'])

    def test_dataframe_required_columns_ok(self):
        wizard = self._create_wizard('partners.csv', b'name,qty\nA,1\n')
        df = pd.DataFrame([{'name': 'A', 'qty': 1}])
        res = wizard.dataframe_required_columns(df, ['name', 'qty'])
        self.assertTrue(res)

    def test_parse_integer(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        self.assertEqual(wizard._parse_integer('12.99', None), 12)
        self.assertEqual(wizard._parse_integer('abc', None), 0)
        self.assertEqual(wizard._parse_integer('-7', None), -7)

    def test_parse_float(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        self.assertEqual(wizard._parse_float('12,50', None), 12.5)
        self.assertEqual(wizard._parse_float('abc', None), 0.0)
        self.assertEqual(wizard._parse_float('-7.25', None), -7.25)

    def test_parse_bool(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        self.assertFalse(wizard._parse_bool('no', None))
        self.assertFalse(wizard._parse_bool('0', None))
        self.assertFalse(wizard._parse_bool('null', None))
        self.assertTrue(wizard._parse_bool('yes', None))

    def test_parse_selection(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        state_field = self.env['import.file']._fields['state']
        res = wizard._parse_selection('simulation', state_field)
        self.assertEqual(res, 'simulation')
        self.assertFalse(wizard._parse_selection('invalid', state_field))

    def test_parse_date(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        self.assertEqual(
            wizard._parse_date(datetime(2026, 4, 8, 12, 30), None),
            '2026-04-08'
        )
        self.assertIsNone(wizard._parse_date('invalid', None))

    def test_parser_transforms_data(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        data = {
            'name': '  Spain  ',
            'code': ' es ',
        }
        parsed, errors = wizard.parser('res.country', data)
        self.assertEqual(parsed['name'], 'Spain')
        self.assertEqual(parsed['code'], 'es')
        self.assertFalse(errors)

    def test_parser_required_error(self):
        wizard = self._create_wizard('partners.csv', b'name\nA\n')
        data = {
            'name': '  ',
        }
        parsed, errors = wizard.parser('res.country', data)
        self.assertEqual(parsed['name'], '')
        self.assertTrue(errors)
        self.assertIn('name', ''.join(errors))

    def test_open_template_form_requires_file(self):
        wizard = self.import_file_model.create({
            'template_id': self.template.id,
            'file_filename': 'partners.csv',
            'file': False,
        })
        with self.assertRaisesRegex(
            UserError, 'You must choose a file to import!'
        ):
            wizard.open_template_form()

    def test_action_open_form_with_view(self):
        wizard = self.import_file_model.create({
            'template_id': self.template_with_model.id,
            'file_filename': 'partners.csv',
            'file': base64.b64encode(b'name\nA\n'),
            'simulate': True,
        })
        model_cls = type(self.env['import.file.line'])
        with patch.object(model_cls, 'get_view', return_value={'view_id': 999}):
            action = self.template_with_model.action_open_form(wizard)
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'import.file.line')
        self.assertEqual(action['target'], 'new')

    def test_action_open_form_without_view(self):
        wizard = self.import_file_model.create({
            'template_id': self.template_with_model.id,
            'file_filename': 'partners.csv',
            'file': base64.b64encode(b'name\nA\n'),
            'simulate': True,
        })
        model_cls = type(self.env['import.file.line'])
        with patch.object(
            model_cls, 'get_view', return_value={}
        ), patch.object(
            model_cls, 'import_file', return_value=True, create=True
        ):
            action = self.template_with_model.action_open_form(wizard)
        self.assertEqual(action['res_model'], 'import.file')
        self.assertEqual(wizard.state, 'simulation')

    def test_action_open_from_simulation_form_step_done(self):
        wizard = self.import_file_model.create({
            'template_id': self.template_with_model.id,
            'file_filename': 'partners.csv',
            'file': base64.b64encode(b'name\nA\n'),
            'simulate': True,
        })
        self.env['import.file.line'].create({'name': 'seed'})
        model_cls = type(self.env['import.file.line'])
        with patch.object(
            model_cls, 'get_view', return_value={'view_id': 999}
        ), patch.object(
            model_cls, 'import_file', return_value=True, create=True
        ):
            action = self.template_with_model.action_open_from_simulation_form(
                wizard)
        self.assertEqual(action['res_model'], 'import.file')
        self.assertEqual(wizard.state, 'step_done')

    def test_action_open_from_simulation_form_orm_error(self):
        wizard = self.import_file_model.create({
            'template_id': self.template_with_model.id,
            'file_filename': 'partners.csv',
            'file': base64.b64encode(b'name\nA\n'),
            'simulate': True,
        })
        self.env['import.file.line'].create({'name': 'seed'})
        model_cls = type(self.env['import.file.line'])
        with patch.object(
            model_cls, 'get_view', return_value={'view_id': 999}
        ), patch.object(
            model_cls, 'import_file', return_value=False, create=True
        ):
            action = self.template_with_model.action_open_from_simulation_form(
                wizard)
        self.assertEqual(action['res_model'], 'import.file')
        self.assertEqual(wizard.state, 'orm_error')
