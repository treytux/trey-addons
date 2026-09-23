###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_active_contract(self, date):
        self.ensure_one()
        contracts = self.env['contract.contract'].search([
            ('invoice_partner_id', '=', self.id),
        ]).filtered(lambda c: not c.date_end or c.date_end <= date)
        active_contract = contracts and contracts[0] or False
        return active_contract
