###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleSessionPayment(models.TransientModel):
    _name = 'sale.session.payment'
    _description = 'Wizard to register payments in a session'

    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
        required=True,
    )
    team_id = fields.Many2one(
        related='session_id.team_id',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
    )
    payment_journal_ids = fields.Many2many(
        related='session_id.team_id.payment_journal_ids',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain='[("id", "in", payment_journal_ids)]',
        string='Payment journal',
        required=True,
    )
    amount = fields.Float(
        string='Amount paid',
    )

    def action_confirm(self):
        self.ensure_one()
        self.session_id.register_payment(
            self.partner_id, self.journal_id, self.amount)
        return {'type': 'ir.actions.act_window_close'}
