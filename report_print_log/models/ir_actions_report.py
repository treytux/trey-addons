###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        user = self.env.user
        report = self
        try:
            _logger.info(
                _('[REPORT][PRINT] user=%s(%s)[ID=%s] report=%s(%s)'),
                user.name, user.login, user.id, report.name, report.report_name
            )
            return super(IrActionsReport, self).render_qweb_pdf(
                res_ids=res_ids, data=data
            )
        except Exception as e:
            _logger.exception(
                _('[REPORT][ERROR] user=%s(%s)[ID=%s] report=%s(%s) error=%s'),
                user.name, user.login, user.id, report.name, report.report_name,
                str(e)
            )
            raise
