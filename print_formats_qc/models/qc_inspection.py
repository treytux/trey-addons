###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class QcInspection(models.Model):
    _inherit = 'qc.inspection'

    def _prepare_inspection_line(self, test, line, fill=None):
        data = super()._prepare_inspection_line(test, line, fill=fill)
        data['display_type'] = line.display_type
        return data
