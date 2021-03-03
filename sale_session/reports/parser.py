###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ReportSaleSessionTicket(models.TransientModel):
    _name = 'report.sale_session.report_sale_session_ticket'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        sale_session_obj = self.env['sale.session']
        report = report_obj._get_report_from_name(
            'sale_session.report_sale_session_ticket',
        )
        selected_sale_sessions = sale_session_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_sale_sessions,
        }
        report = report_obj.browse(self.ids[0])
        return report.render(
            'sale_session.report_sale_session_ticket', docargs)
