###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ReportGeneralLedgerMoveLine(models.TransientModel):
    _inherit = 'report_general_ledger_move_line'
    _order = 'date ASC, entry ASC, id ASC'
