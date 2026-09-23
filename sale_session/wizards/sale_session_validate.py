###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models


class SaleSessionValidate(models.TransientModel):
    _name = 'sale.session.validate'
    _description = 'Wizard to validate a sale session'

    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
        required=True,
        readonly=True,
    )
    company_currency = fields.Many2one(
        related='session_id.company_id.currency_id',
    )
    allow_edit_amount_send = fields.Boolean(
        related='session_id.team_id.allow_edit_amount_send',
    )
    amount_send = fields.Monetary(
        currency_field='company_currency',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal destination',
        domain='[("type", "in", ("cash", "bank"))]',
    )

    def action_confirm(self):
        self.ensure_one()
        self.session_id.write({
            'state': 'validate',
            'validation_date': fields.Datetime.now(),
            'validate_journal_id': self.journal_id.id,
            'amount_send': self.amount_send,
        })
        if self.session_id.mismatch_open_move_ids.filtered(
                lambda m: m.state == 'draft'):
            self.session_id.mismatch_open_move_ids.action_post()
        if self.session_id.mismatch_close_move_ids.filtered(
                lambda m: m.state == 'draft'):
            self.session_id.mismatch_close_move_ids.action_post()
        if not self.amount_send:
            return True
        if not self.journal_id:
            raise exceptions.ValidationError(_(
                'You must select a validation journal for validate this '
                'session'))
        reference = _('Sales session validated %s') % self.session_id.name
        debit_vals = {
            'name': reference,
            'partner_id': self.session_id.company_id.partner_id.id,
            'debit': self.session_id.amount_send,
            'account_id': self.journal_id.default_account_id.id,
        }
        cash_journals = self.session_id.payment_ids.mapped(
            'journal_id').filtered(lambda j: j.type == 'cash')
        if len(cash_journals) > 1:
            raise exceptions.ValidationError(_(
                'This session cannot be validated, you have to perform these '
                'operation manually because there are more than one cash '
                'payment journal.'))
        if not cash_journals:
            cash_journals = self.session_id.team_id.cash_payment_journal_id
        credit_vals = debit_vals.copy()
        credit_vals.update({
            'debit': 0,
            'credit': self.session_id.amount_send,
            'account_id': cash_journals.default_account_id.id,
        })
        self.session_id.validate_move_id = self.env['account.move'].create({
            'date': self.session_id.close_date.date(),
            'ref': reference,
            'journal_id': self.journal_id.id,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
        })
        self.session_id.validate_move_id.action_post()
