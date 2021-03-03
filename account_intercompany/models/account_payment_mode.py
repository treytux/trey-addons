###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    intercompany_map_ids = fields.Many2many(
        domain='[("company_id", "!=", company_id)]',
        comodel_name='account.payment.mode',
        relation='account_payment_mode_intercompany',
        column1='mode_id',
        column2='mapped_id')

    def check_intercompany_map_ids(self):
        for record in self:
            companies = record.intercompany_map_ids.mapped('company_id')
            if len(companies) != len(record.intercompany_map_ids):
                raise UserError(_('Only a record by company'))

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.check_intercompany_map_ids()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        self.check_intercompany_map_ids()
        return res
