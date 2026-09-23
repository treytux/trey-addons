###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io

import pandas as pd
from odoo.tests import common


class TestResPartnerExportFinancialRisk(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.credit_limit = 2500
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner test',
            'is_company': True,
            'vat': 'ESA00000000',
            'credit_limit': self.credit_limit,
        })
        self.partner_02 = self.env['res.partner'].create({
            'name': 'Partner test',
            'is_company': True,
            'vat': 'ESA00000000',
            'credit_limit': self.credit_limit,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 25,
        })
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner_02.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.sale_02.action_confirm()
        self.sale_02.action_invoice_create()

    def test_create_file_one_partner(self):
        self.assertEqual(self.partner_01.credit_limit, self.credit_limit)
        wizard = self.env['res.partner.export.financial.risk'].with_context(
            active_ids=self.partner_01.ids,
            active_id=self.partner_01.ids[0],
        ).create({})
        self.assertFalse(wizard.file)
        self.assertFalse(wizard.filename)
        res = wizard.button_export_financial_risk()
        self.assertEqual(res['type'], 'ir.actions.act_url')
        self.assertEqual(res['target'], 'new')
        self.assertEqual(res['nodestroy'], False)
        url = wizard.set_url_download()
        self.assertEqual(res['url'], url['url'])
        self.assertTrue(wizard.file)
        buf = io.BytesIO()
        buf.write(base64.b64decode(wizard.file))
        buf.seek(0)
        df = pd.read_excel(
            buf, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        rows = len(df.axes[0])
        cols = len(df.axes[1])
        self.assertEqual(rows, 1)
        self.assertEqual(cols, 8)
        self.assertEqual(df.iloc[0][0], self.partner_01.name)
        self.assertEqual(df.iloc[0][1], self.partner_01.vat)
        self.assertEqual(df.iloc[0][2], self.partner_01.credit_limit)
        self.assertEqual(df.iloc[0][3], self.partner_01.risk_invoice_unpaid)
        self.assertEqual(df.iloc[0][4], self.partner_01.risk_invoice_open)
        self.assertEqual(df.iloc[0][5], self.partner_01.risk_sale_order)
        self.assertEqual(df.iloc[0][6], self.partner_01.risk_invoice_draft)
        self.assertEqual(df.iloc[0][7], self.partner_01.risk_total)

    def test_create_file_multiple_partners(self):
        self.assertEqual(self.partner_02.credit_limit, self.credit_limit)
        wizard = self.env['res.partner.export.financial.risk'].with_context(
            active_ids=[self.partner_01.id, self.partner_02.id],
            active_id=self.partner_02.id,
        ).create({})
        self.assertFalse(wizard.file)
        self.assertFalse(wizard.filename)
        res = wizard.button_export_financial_risk()
        self.assertEqual(res['type'], 'ir.actions.act_url')
        self.assertEqual(res['target'], 'new')
        self.assertEqual(res['nodestroy'], False)
        url = wizard.set_url_download()
        self.assertEqual(res['url'], url['url'])
        self.assertTrue(wizard.file)
        buf = io.BytesIO()
        buf.write(base64.b64decode(wizard.file))
        buf.seek(0)
        df = pd.read_excel(
            buf, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        rows = len(df.axes[0])
        cols = len(df.axes[1])
        self.assertEqual(rows, 2)
        self.assertEqual(cols, 8)
        self.assertEqual(df.iloc[0][0], self.partner_01.name)
        self.assertEqual(df.iloc[0][1], self.partner_01.vat)
        self.assertEqual(df.iloc[0][2], self.partner_01.credit_limit)
        self.assertEqual(df.iloc[0][3], self.partner_01.risk_invoice_unpaid)
        self.assertEqual(df.iloc[0][4], self.partner_01.risk_invoice_open)
        self.assertEqual(df.iloc[0][5], self.partner_01.risk_sale_order)
        self.assertEqual(df.iloc[0][6], self.partner_01.risk_invoice_draft)
        self.assertEqual(df.iloc[0][7], self.partner_01.risk_total)
        self.assertEqual(df.iloc[1][0], self.partner_02.name)
        self.assertEqual(df.iloc[1][1], self.partner_02.vat)
        self.assertEqual(df.iloc[1][2], self.partner_02.credit_limit)
        self.assertEqual(df.iloc[1][3], self.partner_02.risk_invoice_unpaid)
        self.assertEqual(df.iloc[1][4], self.partner_02.risk_invoice_open)
        self.assertEqual(df.iloc[1][5], self.partner_02.risk_sale_order)
        self.assertEqual(df.iloc[1][6], self.partner_02.risk_invoice_draft)
        self.assertEqual(df.iloc[1][7], self.partner_02.risk_total)

    def test_create_file_without_partner_vat(self):
        self.assertEqual(self.partner_01.credit_limit, self.credit_limit)
        self.partner_01.vat = False
        wizard = self.env['res.partner.export.financial.risk'].with_context(
            active_ids=self.partner_01.ids,
            active_id=self.partner_01.ids[0],
        ).create({})
        self.assertFalse(wizard.file)
        self.assertFalse(wizard.filename)
        res = wizard.button_export_financial_risk()
        self.assertEqual(res['type'], 'ir.actions.act_url')
        self.assertEqual(res['target'], 'new')
        self.assertEqual(res['nodestroy'], False)
        url = wizard.set_url_download()
        self.assertEqual(res['url'], url['url'])
        self.assertTrue(wizard.file)
        buf = io.BytesIO()
        buf.write(base64.b64decode(wizard.file))
        buf.seek(0)
        df = pd.read_excel(
            buf, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        rows = len(df.axes[0])
        cols = len(df.axes[1])
        self.assertEqual(rows, 1)
        self.assertEqual(cols, 8)
        self.assertFalse(self.partner_01.vat)
        self.assertEqual(df.iloc[0][1], ' ')
