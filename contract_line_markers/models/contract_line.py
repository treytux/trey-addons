###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    @api.multi
    def _insert_markers(self, first_date_invoiced, last_date_invoiced):
        name = super()._insert_markers(
            first_date_invoiced=first_date_invoiced,
            last_date_invoiced=last_date_invoiced
        )
        self.ensure_one()
        name = name.replace(
            '#START_MONTH_INT#',
            first_date_invoiced.strftime('%m'),
        )
        name = name.replace(
            '#END_MONTH_INT#',
            last_date_invoiced.strftime('%m'),
        )
        name = name.replace(
            '#START_MONTH_STR#',
            first_date_invoiced.strftime('%B').capitalize(),
        )
        name = name.replace(
            '#END_MONTH_STR#',
            last_date_invoiced.strftime('%B').capitalize(),
        )
        name = name.replace(
            '#START_YEAR#',
            first_date_invoiced.strftime('%Y'),
        )
        name = name.replace(
            '#END_YEAR#',
            last_date_invoiced.strftime('%Y'),
        )
        return name
