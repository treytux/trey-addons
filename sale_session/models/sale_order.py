###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Session',
    )
    require_sale_session = fields.Boolean(
        related='team_id.require_sale_session',
        string='Require sale session',
    )

    def _check_team_and_session(self):
        if self._context.get('ignore_sale_session'):
            return
        for sale in self:
            if sale.state not in ('draft', 'sent'):
                continue
            if not sale.team_id.require_sale_session:
                continue
            if not sale.session_id:
                raise UserError(_(
                    'Sale team "%s" require a sale session, please set a sale '
                    'session.') % sale.team_id.name)
            if sale.session_id.state != 'open':
                raise UserError(_(
                    'Sale team "%s" require a sale session opened, please '
                    'open a sale session before.') % sale.team_id.name)

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        if 'team_id' not in res:
            return res
        session = self.env['sale.session'].get_current_sale_session(
            res['team_id'])
        if not self.env.user.has_group(
                'sale_session.group_without_sale_session'):
            res['session_id'] = session and session.id or False
        if session and session.team_id.default_partner_id:
            res['partner_id'] = session.team_id.default_partner_id.id
        return res

    @api.onchange('team_id')
    def onchange_team_id(self):
        if not self.env.user.has_group(
                'sale_session.group_without_sale_session'):
            self.session_id = self.team_id.opened_session_id.id

    @api.model
    def create(self, vals):
        sale = super().create(vals)
        sale._check_team_and_session()
        return sale

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        self._check_team_and_session()
        return res

    def action_confirm(self):
        if not self.session_id or not self._context.get('open_wizard'):
            return super().action_confirm()
        session_required = self.team_id.require_sale_session
        if session_required and self.session_id.state != 'open':
            session = self.session_id.get_current_sale_session(self.team_id.id)
            if not session:
                raise UserError(_(
                    'You must open a sale session or change the sale team.'))
            self.session_id = session.id
        self._check_team_and_session()
        return self.open_confirm_and_pay()

    def session_confirm(self):
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_(
                'The sales order must be in draft state, this sales order can '
                'no longer be paid from this wizard. Please perform the '
                'operations manually.'))
        super().action_confirm()
        pickings = self.picking_ids.filtered(
            lambda p: p.state not in ['done', 'cancel'])
        for picking in pickings:
            picking.action_confirm()
            picking.action_assign()
            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            picking.action_done()

    @api.multi
    def session_pay(self, amount, payment_journal):
        self.session_confirm()
        journal = (
            self.session_id.team_id.invoice_journal_ids
            and self.session_id.team_id.invoice_journal_ids[0] or False)
        self.with_context(default_journal_id=journal).action_invoice_create()
        if (not self.partner_id.vat
                and self.session_id.team_id.simplified_journal_id):
            self.invoice_ids.journal_id = (
                self.session_id.team_id.simplified_journal_id.id)
        self.invoice_ids.with_context(bypass_risk=True).action_invoice_open()
        payment = self.env['account.payment'].create({
            'invoice_ids': [(6, 0, self.invoice_ids.ids)],
            'partner_id': self.partner_id.id,
            'sale_session_id': self.session_id.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'amount': amount,
            'communication': '[%s] %s: %s' % (
                self.session_id.name, self.name, self.invoice_ids[-1:].name),
            'journal_id': payment_journal.id,
        })
        payment.action_validate_invoice_payment()
        payment.message_post_with_view(
            'mail.message_origin_link',
            values={'self': payment, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id,
        )

    @api.multi
    def open_confirm_and_pay(self):
        self.ensure_one()
        if not self.session_id:
            raise UserError(_('For confirm and paid must have a sale session.'))
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': self.id,
            'journal_id': (
                self.session_id.team_id.default_payment_journal_id.id),
        })
        action = self.env.ref(
            'sale_session.sale_order_confirm_and_pay_action').read()[0]
        action['res_id'] = wizard.id
        return action
