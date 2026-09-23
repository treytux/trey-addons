###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    @api.multi
    def unlink(self):
        for record in self:
            record.state = 'canceled'
            record.is_canceled = True
        return super().unlink()
