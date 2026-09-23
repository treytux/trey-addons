###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        user = self.env.user
        report = (
            self._get_report_from_name(report_ref)
            if isinstance(report_ref, str) else self)
        try:
            _logger.info(
                _('[REPORT][PRINT] user=%s(%s)[ID=%s] report=%s(%s)'),
                user.name, user.login, user.id, report.name, report.report_name)
            return super()._render_qweb_pdf(
                report_ref, res_ids=res_ids, data=data)
        except Exception as e:
            _logger.exception(
                _('[REPORT][ERROR] user=%s(%s)[ID=%s] report=%s(%s) error=%s'),
                user.name, user.login, user.id, report.name, report.report_name,
                str(e))
            raise
