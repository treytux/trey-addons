###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import os
from unittest.mock import patch

import pandas as pd
from odoo.tests.common import TransactionCase


class TestAccountMoveImportBaxi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.account_sale_tax_id = False
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env.ref(
            'account_move_import_baxi.baxi_product')
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.company.id),
            ('type', '=', 'sale'),
        ], limit=1)
        self.journal.import_account_moves = True

    def get_sample(self, filename):
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'samples', filename)

    def test_import_account_invoice_import_baxi(self):
        fname = self.get_sample('account_invoice_import_baxi.xls')
        if not os.path.exists(fname):
            self.skipTest('Sample file not found')
        with open(fname, 'rb') as f:
            content = base64.b64encode(f.read())
        wizard = self.env['account.move.import_file'].with_context(
            active_model='account.journal',
            active_ids=[self.journal.id],
        ).create({
            'file': content,
            'type': 'baxi',
        })
        baxi_payments = wizard._get_baxi_payments()
        if not baxi_payments:
            buf = io.BytesIO()
            buf.write(base64.b64decode(content))
            buf.seek(0)
            df = pd.read_html(buf, decimal=',', thousands='.')[0]
            df.columns = [col.replace(': ', ':') for col in df.columns]
            for pago in df['PAGO'].unique():
                if pago and str(pago).strip():
                    self.env['account.payment.mode'].create({
                        'name': str(pago),
                        'baxi_name': str(pago).strip(),
                        'payment_method_id': self.env.ref(
                            'account.account_payment_method_manual_in').id,
                        'bank_account_link': 'variable',
                    })
            baxi_payments = wizard._get_baxi_payments()
            self.assertTrue(baxi_payments)
        moves = wizard.import_file()
        self.assertTrue(moves)

    def _make_row(self, name='025-28000000009999'):
        return {
            'DOCF_NUMFACTURA': name,
            'PAGO': 'CONTADO',
            'Fact cobrada': 'No',
            'TipoDesc': 'FACTURA',
            'DOCF_FECHA': '29/01/2021 18:32:46',
            'DOCF_DESCRIP': 'Test invoice',
            'DOCF_SUBTOTAL': 100.0,
            'DOCF_TOTAL': 100.0,
            'Recibo Id': '',
        }

    def test_import_invoice_no_vat_uses_simplified_journal(self):
        partner = self.env['res.partner'].create({
            'name': 'No VAT Partner',
        })
        simplified_journal = self.env['account.journal'].create({
            'name': 'Simplified Journal',
            'type': 'sale',
            'code': 'SIMP',
        })
        self.journal.simplified_journal_id = simplified_journal
        wizard = self.env['account.move.import_file'].new({})
        with patch.object(
                type(wizard), '_partner_search_or_create',
                return_value=partner):
            move = wizard._import_invoice(
                self._make_row(), {'CONTADO': 1}, self.product,
                self.journal)
        self.assertTrue(move)
        self.assertEqual(move.journal_id, simplified_journal)

    def test_import_invoice_with_vat_keeps_original_journal(self):
        partner = self.env['res.partner'].create({
            'name': 'VAT Partner',
            'vat': 'ESB12345674',
        })
        simplified_journal = self.env['account.journal'].create({
            'name': 'Simplified Journal',
            'type': 'sale',
            'code': 'SIMP2',
        })
        self.journal.simplified_journal_id = simplified_journal
        wizard = self.env['account.move.import_file'].new({})
        with patch.object(
                type(wizard), '_partner_search_or_create',
                return_value=partner):
            move = wizard._import_invoice(
                self._make_row('025-28000000009998'),
                {'CONTADO': 1}, self.product, self.journal)
        self.assertTrue(move)
        self.assertEqual(move.journal_id, self.journal)

    def test_import_invoice_no_vat_no_simplified_journal(self):
        partner = self.env['res.partner'].create({
            'name': 'No VAT Partner',
        })
        wizard = self.env['account.move.import_file'].new({})
        with patch.object(
                type(wizard), '_partner_search_or_create',
                return_value=partner):
            move = wizard._import_invoice(
                self._make_row('025-28000000009997'),
                {'CONTADO': 1}, self.product, self.journal)
        self.assertTrue(move)
        self.assertEqual(move.journal_id, self.journal)
