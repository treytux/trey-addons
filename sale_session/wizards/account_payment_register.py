###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import Command, api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    sale_session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
        domain='[("state", "=", "open")]',
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        sales_team = self.env['crm.team'].search([
            ('member_ids', 'in', self.env.user.ids),
        ])
        if not sales_team:
            return res
        session = self.env['sale.session'].get_current_sale_session(
            sales_team.id)
        if not self.env.user.has_group(
                'sale_session.group_without_sale_session'):
            res['sale_session_id'] = session and session.id or False
        return res

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_account_id = self._context.get('payment_account_id', False)
        if payment_account_id and not vals.get('payment_account_id'):
            vals['force_session_outstanding_account_id'] = payment_account_id.id
        if self.sale_session_id:
            vals['sale_session_id'] = self.sale_session_id.id
        return vals

    def action_create_payments(self):
        if (self.env.user.has_group('sale_session.group_user_sale_session')
                and not self.env.user.has_group('account.group_account_invoice')
                and self.sale_session_id):
            return super(
                AccountPaymentRegister, self.sudo()).action_create_payments()
        return super().action_create_payments()

    def _compute_available_journal_ids(self):
        res = super()._compute_available_journal_ids()
        sales_team = self.env['crm.team'].search([
            ('member_ids', 'in', self.env.user.ids),
        ])
        if not sales_team:
            return res
        available_journals = sales_team.payment_journal_ids
        for wizard in self:
            wizard.available_journal_ids = [
                Command.set(available_journals.ids)]
        return res
