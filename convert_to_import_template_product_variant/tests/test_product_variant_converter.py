###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os
from io import BytesIO

import pandas as pd
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductVariantConverter(TransactionCase):
    def setUp(self):
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser@example.com',
            'password': 'testuser',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def create_wizard(self, fname, supplier):
        file = base64.b64encode(open(fname, 'rb').read())
        return self.env['product.variant.converter.wizard'].create({
            'supplier': supplier,
            'input_file': file,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_brooks_ok(self):
        fname = self.get_sample('test_brooks_ok.xlsx')
        wizard = self.create_wizard(fname, 'brooks')
        wizard.with_user(self.test_user).action_accept()
        self.assertTrue(wizard.output_file)
        file_content = base64.b64decode(wizard.output_file)
        excel_file = BytesIO(file_content)
        df = pd.read_excel(
            excel_file, converters={
                'barcode': str,
                'standard_price': str,
            })
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertIn('product_tmpl_code', df.columns)
        self.assertIn('default_code', df.columns)
        self.assertIn('barcode', df.columns)
        self.assertEqual(df['product_tmpl_code'].iloc[0], '1000491D681')
        self.assertEqual(df['default_code'].iloc[0], '1000491D681')
        self.assertEqual(
            df['attribute: Color'].iloc[0], 'Pink Clay/Atomizer Blue')
        self.assertEqual(df['attribute: Size'].iloc[0], 37.5)
        self.assertEqual(df['name'].iloc[0], 'Hyperion Elite 5')
        self.assertEqual(
            f"{float(df['standard_price'].iloc[0]):.2f} €", '137.50 €')
        self.assertEqual(
            f"{float(df['*TMPL*list_price'].iloc[0]):.2f} €", '275.00 €')
        self.assertEqual(df['weight'].iloc[0], 0.4717360648)
        self.assertEqual(df['barcode'].iloc[0], '0195394690217')
        self.assertEqual(df['categ_id'].iloc[0], 'All')
        self.assertEqual(df['type'].iloc[0], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[0], 'delivery')
        self.assertEqual(df['uom_id'].iloc[0], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[0], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[1], '1204261B020')
        self.assertEqual(df['default_code'].iloc[1], '1204261B020')
        self.assertEqual(df['attribute: Color'].iloc[1], 'Black/Black/Ebony')
        self.assertEqual(df['attribute: Size'].iloc[1], 35.5)
        self.assertEqual(df['name'].iloc[1], 'Adrenaline GTS 24 Woman')
        self.assertEqual(
            f"{float(df['standard_price'].iloc[1]):.2f} €", '75.00 €')
        self.assertEqual(
            f"{float(df['*TMPL*list_price'].iloc[1]):.2f} €", '150.00 €')
        self.assertEqual(df['weight'].iloc[1], 0.52389918735)
        self.assertEqual(df['barcode'].iloc[1], '0195394534245')
        self.assertEqual(df['categ_id'].iloc[1], 'All')
        self.assertEqual(df['type'].iloc[1], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[1], 'delivery')
        self.assertEqual(df['uom_id'].iloc[1], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[1], 'Units')

    def test_brooks_empty_file(self):
        fname = self.get_sample('test_brooks_empty_file.xlsx')
        wizard = self.create_wizard(fname, 'brooks')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual('File sheets are empty.', result.exception.args[0])

    def test_brooks_duplicate_columns(self):
        fname = self.get_sample('test_brooks_duplicate_columns.xlsx')
        wizard = self.create_wizard(fname, 'brooks')
        with self.assertRaises(UserError) as context:
            wizard.action_accept()
        self.assertEqual(
            str(context.exception),
            'Error, duplicate columns in sheets: \'Pricat Completo\': EAN'
        )

    def test_brooks_wrong_file_type(self):
        fname = self.get_sample('test_brooks_wrong_file_type.txt')
        wizard = self.create_wizard(fname, 'brooks')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Invalid file type. Please upload an Excel file.',
            result.exception.args[0])

    def test_brooks_no_pricelist_sheet(self):
        fname = self.get_sample('test_brooks_no_pricelist_sheet.xlsx')
        wizard = self.create_wizard(fname, 'brooks')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain a sheet named \'Pricelist\'.',
            result.exception.args[0]
        )

    def test_brooks_no_pricat_complete_sheet(self):
        fname = self.get_sample('test_brooks_no_pricat_complete_sheet.xlsx')
        wizard = self.create_wizard(fname, 'brooks')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain a sheet named \'Pricat Completo\'.',
            result.exception.args[0]
        )

    def test_brooks_no_column(self):
        fname = self.get_sample('test_brooks_no_column.xlsx')
        wizard = self.create_wizard(fname, 'brooks')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain columns: EAN', result.exception.args[0])

    def test_brooks_no_column_row(self):
        fname = self.get_sample('test_brooks_no_column_row.xlsx')
        wizard = self.create_wizard(fname, 'brooks')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Column \'EAN\' is empty in rows: 3', result.exception.args[0])

    def test_salomon_ok(self):
        fname = self.get_sample('test_salomon_ok.xlsx')
        wizard = self.create_wizard(fname, 'salomon')
        wizard.with_user(self.test_user).action_accept()
        self.assertTrue(wizard.output_file)
        file_content = base64.b64decode(wizard.output_file)
        excel_file = BytesIO(file_content)
        df = pd.read_excel(
            excel_file, converters={
                'barcode': str,
            })
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertIn('product_tmpl_code', df.columns)
        self.assertIn('default_code', df.columns)
        self.assertIn('barcode', df.columns)
        self.assertEqual(df['product_tmpl_code'].iloc[0], 'L47820400')
        self.assertEqual(df['default_code'].iloc[0], 'L47820400')
        self.assertEqual(df['attribute: Color'].iloc[0], 'Yellow')
        self.assertEqual(df['attribute: Size'].iloc[0], 5)
        self.assertEqual(
            df['name'].iloc[0],
            'CALZADO Bajo GENESIS W Fuco/Tender/Black Woman'
        )
        self.assertEqual(df['standard_price'].iloc[0], 64.0666)
        self.assertEqual(df['*TMPL*list_price'].iloc[0], 150.00)
        self.assertEqual(df['barcode'].iloc[0], '00195751930505')
        self.assertEqual(df['categ_id'].iloc[0], 'All')
        self.assertEqual(df['type'].iloc[0], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[0], 'delivery')
        self.assertEqual(df['uom_id'].iloc[0], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[0], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[1], 'L47807600')
        self.assertEqual(df['default_code'].iloc[1], 'L47807600')
        self.assertEqual(df['attribute: Color'].iloc[1], 'Red')
        self.assertEqual(df['attribute: Size'].iloc[1], 10)
        self.assertEqual(
            df['name'].iloc[1],
            'CALZADO Bajo GENESIS Bk/Alloy/Tume'
        )
        self.assertEqual(df['*TMPL*list_price'].iloc[1], 150)
        self.assertEqual(df['barcode'].iloc[1], '00195751929776')
        self.assertEqual(df['categ_id'].iloc[1], 'All')
        self.assertEqual(df['type'].iloc[1], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[1], 'delivery')
        self.assertEqual(df['uom_id'].iloc[1], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[1], 'Units')

    def test_salomon_empty_file(self):
        fname = self.get_sample('test_salomon_empty_file.xlsx')
        wizard = self.create_wizard(fname, 'salomon')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual('File sheets are empty.', result.exception.args[0])

    def test_salomon_wrong_file_type(self):
        fname = self.get_sample('test_salomon_wrong_file_type.txt')
        wizard = self.create_wizard(fname, 'salomon')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Invalid file type. Please upload an Excel file.',
            result.exception.args[0])

    def test_salomon_no_column(self):
        fname = self.get_sample('test_salomon_no_column.xlsx')
        wizard = self.create_wizard(fname, 'salomon')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain columns: Color', result.exception.args[0])

    def test_salomon_no_column_row(self):
        fname = self.get_sample('test_salomon_no_column_row.xlsx')
        wizard = self.create_wizard(fname, 'salomon')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Column \'Color\' is empty in rows: 2', result.exception.args[0])

    def test_salomon_duplicate_columns(self):
        fname = self.get_sample('test_salomon_duplicate_columns.xlsx')
        wizard = self.create_wizard(fname, 'salomon')
        with self.assertRaises(UserError) as context:
            wizard.action_accept()
        self.assertEqual(
            str(context.exception),
            'Error, duplicate columns in sheets: \'Worksheet\': Código SAP'
        )

    def test_asics_ok(self):
        fname = self.get_sample('test_asics_ok.xlsx')
        wizard = self.create_wizard(fname, 'asics')
        wizard.with_user(self.test_user).action_accept()
        self.assertTrue(wizard.output_file)
        file_content = base64.b64decode(wizard.output_file)
        excel_file = BytesIO(file_content)
        df = pd.read_excel(
            excel_file, converters={
                'barcode': str,
            })
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertIn('product_tmpl_code', df.columns)
        self.assertIn('default_code', df.columns)
        self.assertIn('barcode', df.columns)
        self.assertEqual(df['product_tmpl_code'].iloc[0], '2012D140')
        self.assertEqual(df['default_code'].iloc[0], '2012D140')
        self.assertEqual(df['attribute: Color'].iloc[0], 'INDIGO FOG')
        self.assertEqual(df['attribute: Size'].iloc[0], 'XS')
        self.assertEqual(df['barcode'].iloc[0], '4570158682046')
        self.assertEqual(
            df['name'].iloc[0], 'NAGINO RUN ADJUSTABLE  SS TOP Woman')
        self.assertEqual(df['standard_price'].iloc[0], 22.5)
        self.assertEqual(df['*TMPL*list_price'].iloc[0], 45.00)
        self.assertEqual(df['weight'].iloc[0], 92.000)
        self.assertEqual(df['categ_id'].iloc[0], 'All')
        self.assertEqual(df['type'].iloc[0], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[0], 'delivery')
        self.assertEqual(df['uom_id'].iloc[0], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[0], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[1], '3013A980')
        self.assertEqual(df['default_code'].iloc[1], '3013A980')
        self.assertEqual(
            df['attribute: Color'].iloc[1], 'OYSTER WHITE/SANDSTORM')
        self.assertEqual(df['attribute: Size'].iloc[1], 'I')
        self.assertEqual(df['barcode'].iloc[1], '4571633031045')
        self.assertEqual(
            df['name'].iloc[1], 'PERFORMANCE RUN SOCK QUARTER')
        self.assertEqual(df['standard_price'].iloc[1], 9.0)
        self.assertEqual(df['*TMPL*list_price'].iloc[1], 18)
        self.assertEqual(df['weight'].iloc[1], 69)
        self.assertEqual(df['categ_id'].iloc[1], 'All')
        self.assertEqual(df['type'].iloc[1], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[1], 'delivery')
        self.assertEqual(df['uom_id'].iloc[1], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[1], 'Units')

    def test_asics_empty_file(self):
        fname = self.get_sample('test_asics_empty_file.xlsx')
        wizard = self.create_wizard(fname, 'asics')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual('File sheets are empty.', result.exception.args[0])

    def test_asics_wrong_file_type(self):
        fname = self.get_sample('test_asics_wrong_file_type.txt')
        wizard = self.create_wizard(fname, 'asics')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Invalid file type. Please upload an Excel file.',
            result.exception.args[0])

    def test_asics_no_column(self):
        fname = self.get_sample('test_asics_no_column.xlsx')
        wizard = self.create_wizard(fname, 'asics')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain columns: ZZTRADING_CODE',
            result.exception.args[0],
        )

    def test_asics_no_column_row(self):
        fname = self.get_sample('test_asics_no_column_row.xlsx')
        wizard = self.create_wizard(fname, 'asics')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Column \'ZZTRADING_CODE\' is empty in rows: 2',
            result.exception.args[0],
        )

    def test_asics_duplicate_columns(self):
        fname = self.get_sample('test_asics_duplicate_columns.xlsx')
        wizard = self.create_wizard(fname, 'asics')
        with self.assertRaises(UserError) as context:
            wizard.action_accept()
        self.assertEqual(
            str(context.exception),
            'Error, duplicate columns in sheets: \'Sheet1\': ZZTRADING_CODE'
        )

    def test_new_balance_ok(self):
        fname = self.get_sample('test_new_balance_ok.xlsx')
        wizard = self.create_wizard(fname, 'new_balance')
        wizard.with_user(self.test_user).action_accept()
        self.assertTrue(wizard.output_file)
        file_content = base64.b64decode(wizard.output_file)
        excel_file = BytesIO(file_content)
        df = pd.read_excel(
            excel_file, converters={
                'barcode': str,
            })
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertIn('product_tmpl_code', df.columns)
        self.assertIn('default_code', df.columns)
        self.assertIn('barcode', df.columns)
        self.assertEqual(df['product_tmpl_code'].iloc[0], 'W880V15')
        self.assertEqual(df['default_code'].iloc[0], 'W880V15')
        self.assertEqual(df['attribute: Color'].iloc[0], 'REFLECTION')
        self.assertEqual(df['attribute: Size'].iloc[0], '05(35)')
        self.assertEqual(df['barcode'].iloc[0], '0198686636948')
        self.assertEqual(df['name'].iloc[0], 'Fresh Foam X 880v15')
        self.assertEqual(df['standard_price'].iloc[0], 80)
        self.assertEqual(df['*TMPL*list_price'].iloc[0], 64.09)
        self.assertEqual(df['categ_id'].iloc[0], 'All')
        self.assertEqual(df['type'].iloc[0], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[0], 'delivery')
        self.assertEqual(df['uom_id'].iloc[0], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[0], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[1], 'W880V15')
        self.assertEqual(df['default_code'].iloc[1], 'W880V15')
        self.assertEqual(df['attribute: Color'].iloc[1], 'REFLECTION')
        self.assertEqual(df['attribute: Size'].iloc[1], '055(36)')
        self.assertEqual(df['barcode'].iloc[1], '0198686636955')
        self.assertEqual(df['name'].iloc[1], 'Fresh Foam X 880v15 Woman')
        self.assertEqual(df['standard_price'].iloc[1], 80)
        self.assertEqual(df['*TMPL*list_price'].iloc[1], 64.07)
        self.assertEqual(df['categ_id'].iloc[1], 'All')
        self.assertEqual(df['type'].iloc[1], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[1], 'delivery')
        self.assertEqual(df['uom_id'].iloc[1], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[1], 'Units')

    def test_new_balance_empty_file(self):
        fname = self.get_sample('test_new_balance_empty_file.xlsx')
        wizard = self.create_wizard(fname, 'new_balance')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual('File sheets are empty.', result.exception.args[0])

    def test_new_balance_wrong_file_type(self):
        fname = self.get_sample('test_new_balance_wrong_file_type.txt')
        wizard = self.create_wizard(fname, 'new_balance')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Invalid file type. Please upload an Excel file.',
            result.exception.args[0])

    def test_new_balance_no_column(self):
        fname = self.get_sample('test_new_balance_no_column.xlsx')
        wizard = self.create_wizard(fname, 'new_balance')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain columns: Style Number',
            result.exception.args[0],
        )

    def test_new_balance_no_column_row(self):
        fname = self.get_sample('test_new_balance_no_column_row.xlsx')
        wizard = self.create_wizard(fname, 'new_balance')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Column \'Style Number\' is empty in rows: 3',
            result.exception.args[0],
        )

    def test_new_balance_duplicate_columns(self):
        fname = self.get_sample('test_new_balance_duplicate_columns.xlsx')
        wizard = self.create_wizard(fname, 'new_balance')
        with self.assertRaises(UserError) as context:
            wizard.action_accept()
        self.assertEqual(
            str(context.exception),
            "Error, duplicate columns in sheets: \'Pedido Elastic\':"
            " Style Number"
        )

    def test_hoka_ok(self):
        fname = self.get_sample('test_hoka_ok.xlsx')
        wizard = self.create_wizard(fname, 'hoka')
        wizard.with_user(self.test_user).action_accept()
        self.assertTrue(wizard.output_file)
        file_content = base64.b64decode(wizard.output_file)
        excel_file = BytesIO(file_content)
        df = pd.read_excel(
            excel_file, converters={
                'barcode': str,
                'product_tmpl_code': str,
                'default_code': str,
            })
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertIn('product_tmpl_code', df.columns)
        self.assertIn('default_code', df.columns)
        self.assertIn('barcode', df.columns)
        self.assertEqual(df['product_tmpl_code'].iloc[0], '1122930')
        self.assertEqual(df['default_code'].iloc[0], '1122930')
        self.assertEqual(df['attribute: Color'].iloc[0], 'WHITE')
        self.assertEqual(df['attribute: Size'].iloc[0], 'L')
        self.assertEqual(df['barcode'].iloc[0], '0198605003622')
        self.assertEqual(df['name'].iloc[0], 'CALCETIN U NO-SHOW RUN SOCK 3PK')
        self.assertEqual(df['standard_price'].iloc[0], 13.2)
        self.assertEqual(df['*TMPL*list_price'].iloc[0], 30)
        self.assertEqual(df['categ_id'].iloc[0], 'All')
        self.assertEqual(df['type'].iloc[0], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[0], 'delivery')
        self.assertEqual(df['uom_id'].iloc[0], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[0], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[1], '1122930')
        self.assertEqual(df['default_code'].iloc[1], '1122930')
        self.assertEqual(df['attribute: Color'].iloc[1], 'WHITE')
        self.assertEqual(df['attribute: Size'].iloc[1], 'M')
        self.assertEqual(df['barcode'].iloc[1], '0198605003639')
        self.assertEqual(
            df['name'].iloc[1], 'CALCETIN U NO-SHOW RUN SOCK 3PK Woman')
        self.assertEqual(df['standard_price'].iloc[1], 13.2)
        self.assertEqual(df['*TMPL*list_price'].iloc[1], 30)
        self.assertEqual(df['categ_id'].iloc[1], 'All')
        self.assertEqual(df['type'].iloc[1], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[1], 'delivery')
        self.assertEqual(df['uom_id'].iloc[1], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[1], 'Units')

    def test_hoka_empty_file(self):
        fname = self.get_sample('test_hoka_empty_file.xlsx')
        wizard = self.create_wizard(fname, 'hoka')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual('File sheets are empty.', result.exception.args[0])

    def test_hoka_wrong_file_type(self):
        fname = self.get_sample('test_hoka_wrong_file_type.txt')
        wizard = self.create_wizard(fname, 'hoka')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Invalid file type. Please upload an Excel file.',
            result.exception.args[0])

    def test_hoka_no_column(self):
        fname = self.get_sample('test_hoka_no_column.xlsx')
        wizard = self.create_wizard(fname, 'hoka')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain columns: EAN',
            result.exception.args[0],
        )

    def test_hoka_no_column_row(self):
        fname = self.get_sample('test_hoka_no_column_row.xlsx')
        wizard = self.create_wizard(fname, 'hoka')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Column \'REFERENCIA\' is empty in rows: 2',
            result.exception.args[0],
        )

    def test_hoka_duplicate_columns(self):
        fname = self.get_sample('test_hoka_duplicate_columns.xlsx')
        wizard = self.create_wizard(fname, 'hoka')
        with self.assertRaises(UserError) as context:
            wizard.action_accept()
        self.assertEqual(
            str(context.exception),
            'Error, duplicate columns in sheets: \'K25\': TALLA'
        )

    def test_mizuno_ok(self):
        fname = self.get_sample('test_mizuno_ok.xlsx')
        wizard = self.create_wizard(fname, 'mizuno')
        wizard.with_user(self.test_user).action_accept()
        self.assertTrue(wizard.output_file)
        file_content = base64.b64decode(wizard.output_file)
        excel_file = BytesIO(file_content)
        df = pd.read_excel(
            excel_file, converters={
                'barcode': str,
                'product_tmpl_code': str,
                'attribute: Size': str,
            })
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 6)
        self.assertIn('product_tmpl_code', df.columns)
        self.assertIn('default_code', df.columns)
        self.assertIn('barcode', df.columns)
        self.assertEqual(df['product_tmpl_code'].iloc[0], '61GA2432')
        self.assertEqual(df['default_code'].iloc[0], '61GA2432')
        self.assertEqual(
            df['attribute: Color'].iloc[0],
            'White/Baritone Blue/CalypsoCor'
        )
        self.assertEqual(df['attribute: Size'].iloc[0], '39')
        self.assertEqual(df['barcode'].iloc[0], '5059882571486')
        self.assertEqual(df['name'].iloc[0], 'WAVE ENFORCE COURT AC Woman')
        self.assertEqual(df['standard_price'].iloc[0], 55)
        self.assertEqual(df['*TMPL*list_price'].iloc[0], 110)
        self.assertEqual(df['categ_id'].iloc[0], 'All')
        self.assertEqual(df['type'].iloc[0], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[0], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[0], 'delivery')
        self.assertEqual(df['uom_id'].iloc[0], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[0], 'Units')
        self.assertEqual(df['attribute: Size'].iloc[1], '40')
        self.assertEqual(df['barcode'].iloc[1], '5059882571493')
        self.assertEqual(df['name'].iloc[1], 'WAVE ENFORCE COURT AC')
        self.assertEqual(df['standard_price'].iloc[1], 55)
        self.assertEqual(df['*TMPL*list_price'].iloc[1], 110)
        self.assertEqual(df['categ_id'].iloc[1], 'All')
        self.assertEqual(df['type'].iloc[1], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[1], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[1], 'delivery')
        self.assertEqual(df['uom_id'].iloc[1], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[1], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[2], '62GAC500')
        self.assertEqual(df['default_code'].iloc[2], '62GAC500')
        self.assertEqual(df['attribute: Color'].iloc[2], 'Odyssey Gray')
        self.assertEqual(df['attribute: Size'].iloc[2], 'L')
        self.assertEqual(df['barcode'].iloc[2], '5059882668322')
        self.assertEqual(df['name'].iloc[2], 'Daybreakers Shadow SS Tee')
        self.assertEqual(df['standard_price'].iloc[2], 27.5)
        self.assertEqual(df['*TMPL*list_price'].iloc[2], 55)
        self.assertEqual(df['categ_id'].iloc[2], 'All')
        self.assertEqual(df['type'].iloc[2], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[2], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[2], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[2], 'delivery')
        self.assertEqual(df['uom_id'].iloc[2], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[2], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[3], '62GAC500')
        self.assertEqual(df['default_code'].iloc[3], '62GAC500')
        self.assertEqual(df['attribute: Color'].iloc[3], 'Odyssey Gray')
        self.assertEqual(df['attribute: Size'].iloc[3], 'M')
        self.assertEqual(df['barcode'].iloc[3], '5059882668308')
        self.assertEqual(df['name'].iloc[3], 'Daybreakers Shadow SS Tee Woman')
        self.assertEqual(df['standard_price'].iloc[3], 27.5)
        self.assertEqual(df['*TMPL*list_price'].iloc[3], 55)
        self.assertEqual(df['categ_id'].iloc[3], 'All')
        self.assertEqual(df['type'].iloc[3], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[3], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[3], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[3], 'delivery')
        self.assertEqual(df['uom_id'].iloc[3], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[3], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[4], 'A2GW0555Z')
        self.assertEqual(df['default_code'].iloc[4], 'A2GW0555Z')
        self.assertEqual(df['attribute: Color'].iloc[4], 'Black/Red')
        self.assertEqual(df['attribute: Size'].iloc[4], 'NS')
        self.assertEqual(df['barcode'].iloc[4], '5054698965634')
        self.assertEqual(df['name'].iloc[4], 'BT Knit Cap')
        self.assertEqual(df['standard_price'].iloc[4], 14)
        self.assertEqual(df['*TMPL*list_price'].iloc[4], 28)
        self.assertEqual(df['categ_id'].iloc[4], 'All')
        self.assertEqual(df['type'].iloc[4], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[4], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[4], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[4], 'delivery')
        self.assertEqual(df['uom_id'].iloc[4], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[4], 'Units')
        self.assertEqual(df['product_tmpl_code'].iloc[5], 'A2GWA570Z')
        self.assertEqual(df['default_code'].iloc[5], 'A2GWA570Z')
        self.assertEqual(df['attribute: Color'].iloc[5], 'Black')
        self.assertEqual(df['attribute: Size'].iloc[5], 'NS')
        self.assertEqual(df['barcode'].iloc[5], '5059431549812')
        self.assertEqual(df['name'].iloc[5], 'BT Neck Warmer Panel Woman')
        self.assertEqual(df['standard_price'].iloc[5], 12.50)
        self.assertEqual(df['*TMPL*list_price'].iloc[5], 25)
        self.assertEqual(df['categ_id'].iloc[5], 'All')
        self.assertEqual(df['type'].iloc[5], 'product')
        self.assertEqual(df['*TMPL*sale_ok'].iloc[5], True)
        self.assertEqual(df['*TMPL*purchase_ok'].iloc[5], True)
        self.assertEqual(df['*TMPL*invoice_policy'].iloc[5], 'delivery')
        self.assertEqual(df['uom_id'].iloc[5], 'Units')
        self.assertEqual(df['uom_po_id'].iloc[5], 'Units')

    def test_mizuno_empty_file(self):
        fname = self.get_sample('test_mizuno_empty_file.xlsx')
        wizard = self.create_wizard(fname, 'mizuno')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual('File sheets are empty.', result.exception.args[0])

    def test_mizuno_wrong_file_type(self):
        fname = self.get_sample('test_mizuno_wrong_file_type.txt')
        wizard = self.create_wizard(fname, 'mizuno')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Invalid file type. Please upload an Excel file.',
            result.exception.args[0])

    def test_mizuno_no_column(self):
        fname = self.get_sample('test_mizuno_no_column.xlsx')
        wizard = self.create_wizard(fname, 'mizuno')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'File must contain columns: EAN',
            result.exception.args[0],
        )

    def test_mizuno_no_column_row(self):
        fname = self.get_sample('test_mizuno_no_column_row.xlsx')
        wizard = self.create_wizard(fname, 'mizuno')
        with self.assertRaises(UserError) as result:
            wizard.action_accept()
        self.assertEqual(
            'Column \'Código Artículo\' is empty in rows: 2',
            result.exception.args[0],
        )

    def test_mizuno_duplicate_columns(self):
        fname = self.get_sample('test_mizuno_duplicate_columns.xlsx')
        wizard = self.create_wizard(fname, 'mizuno')
        with self.assertRaises(UserError) as context:
            wizard.action_accept()
        self.assertEqual(
            str(context.exception),
            "Error, duplicate columns in sheets: 'Calzado': Descripción; "
            "'Apparel & Accesorios': Talla"
        )

    def test_mizuno_parse_price_error(self):
        fname = self.get_sample('test_mizuno_parse_price_error.xlsx')
        wizard = self.create_wizard(fname, 'mizuno')
        with self.assertRaises(UserError) as error:
            wizard.action_accept()
        self.assertEqual(
            error.exception.args[0],
            'Error parsing price. Please check the format. Ensure that the '
            'price is a valid number. Column \'PRECIO TARIFA\', rows: 2.'
        )
