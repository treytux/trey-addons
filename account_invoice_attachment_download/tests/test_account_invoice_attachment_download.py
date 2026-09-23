###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import zipfile

from odoo.tests.common import TransactionCase


class TestAccountInvoiceAttachmentDownload(TransactionCase):

    def test_download_attach(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner test VAT',
            'vat': 'NUMBER',
        })
        partner_novat = self.env['res.partner'].create({
            'name': 'Partner test NO VAT',
            'vat': False,
        })
        journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TJ',
        })
        invoices = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': journal.id,
            'partner_id': partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoices.action_post()
        invoices |= self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': journal.id,
            'partner_id': partner_novat.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoices[1].action_post()
        self.env['ir.attachment'].create({
            'name': '001.pdf',
            'datas': base64.b64encode(b'CONTENT-001'),
            'res_model': 'account.move',
            'res_id': invoices[0].id,
        })
        self.env['ir.attachment'].create({
            'name': '002.pdf',
            'datas': base64.b64encode(b'CONTENT-002'),
            'res_model': 'account.move',
            'res_id': invoices[1].id,
        })
        wizard_obj = self.env['account.move.attachment_download'].with_context(
            active_ids=invoices.ids)
        wizard = wizard_obj.create({})
        wizard.button_attachment_download()
        content = wizard.file_data
        files = zipfile.ZipFile(io.BytesIO(base64.b64decode(content)))
        self.assertEqual(len(files.filelist), 2)
        self.assertEqual(files.filelist[0].filename, '002.pdf')
        self.assertEqual(files.filelist[1].filename, '001.pdf')
        self.assertEqual(files.read('001.pdf'), b'CONTENT-001')
        self.assertEqual(files.read('002.pdf'), b'CONTENT-002')
