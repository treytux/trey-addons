###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestReportPrintLog(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.report = self.env['ir.actions.report'].search([], limit=1)

    def test_report_print(self):
        pdf = self.report._render_qweb_pdf(
            self.report.report_name, res_ids=self.partner.ids)
        self.assertTrue(pdf)
        self.assertTrue(isinstance(pdf, tuple))

    def test_report_error_logging(self):
        with patch(
            'odoo.addons.base.models.ir_actions_report.'
            'IrActionsReport._render_qweb_pdf',
            side_effect=Exception('Forced test error')
        ):
            with self.assertRaises(Exception):
                self.report._render_qweb_pdf(self.partner.ids)
