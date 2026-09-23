###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class L10nEsAeatReportExportToBoe(models.TransientModel):
    _inherit = 'l10n.es.aeat.report.export_to_boe'

    def _export_simple_record(self, line, val):
        active_model = self._context.get('active_model', False)
        if (active_model != 'l10n.es.aeat.mod369.report'
                or line.export_type != 'float' or val != ' '):
            return super()._export_simple_record(line, val)
        align = '>' if line.alignment == 'right' else '<'
        return self._format_string(val or '', line.size, align=align)
