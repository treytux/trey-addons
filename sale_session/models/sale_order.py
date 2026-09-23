###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    team_id = fields.Many2one(
        copy=False,
    )
    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Session',
        tracking=True,
        copy=False,
    )
    require_sale_session = fields.Boolean(
        related='team_id.require_sale_session',
        string='Require sale session',
    )
    sale_session_payment_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Payment journals',
        help='Payment journals used in the sale session wizard.',
        readonly=True,
        copy=False,
    )
    show_confirm_current_session_button = fields.Boolean(
        related='company_id.show_confirm_current_session_button',
        string='Show confirm current session button',
        readonly=True,
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
        sales_team = self.env['crm.team'].search([
            ('member_ids', 'in', self.env.user.ids),
        ])
        if not sales_team:
            return res
        session = self.env['sale.session'].get_current_sale_session(
            sales_team.id)
        if not self.env.user.has_group(
                'sale_session.group_without_sale_session'):
            res['session_id'] = session and session.id or False
        if session and session.team_id.default_partner_id:
            res['partner_id'] = session.team_id.default_partner_id.id
        if session and session.team_id.warehouse_ids:
            res['warehouse_id'] = session.team_id.warehouse_ids[0].id
        return res

    @api.onchange('team_id')
    def onchange_team_id(self):
        if not self.env.user.has_group(
                'sale_session.group_without_sale_session'):
            self.session_id = self.team_id.opened_session_id.id

    @api.onchange('session_id')
    def onchange_session_id(self):
        if not self.session_id:
            return
        if self.session_id.team_id.warehouse_ids:
            self.warehouse_id = self.session_id.team_id.warehouse_ids[0].id

    @api.model_create_multi
    def create(self, vals):
        sale = super().create(vals)
        sale._check_team_and_session()
        return sale

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

    def _check_sale_session_confirm_conditions(self):
        if self.picking_ids.filtered(lambda p: p.state == 'cancel'):
            raise UserError(_(
                'Product deliveries already exist but are canceled, this sales '
                'order can no longer be done from this wizard. Please perform '
                'the operations manually.'))
        if ('done' in self.picking_ids.mapped('state')
                and self.order_line.filtered(
                    lambda ln: ln.qty_delivered != ln.product_uom_qty)):
            raise UserError(_(
                'Product deliveries already exist and are done but not all '
                'products are delivered, this sales order can no longer be done'
                ' from this wizard. Please perform the operations manually.'))
        if self.picking_ids.filtered(
                lambda p: p.picking_type_code != 'outgoing'):
            raise UserError(_(
                'Return deliveries already exist, this sales order can no '
                'longer be done from this wizard. Please perform the operations'
                ' manually.'))
        if self.invoice_ids:
            raise UserError(_(
                'Invoices already exist, this sales order can no longer be '
                'done from this wizard. Please perform the operations '
                'manually.'))

    def session_confirm(self):
        self.ensure_one()
        self._check_sale_session_confirm_conditions()
        if self.state != 'sale':
            if self.env.context.get('open_wizard', False):
                context = self.env.context.copy()
                context['open_wizard'] = False
                self.env.context = context
            res = self.action_confirm()
            if res is not True:
                return res
        pickings = self.picking_ids.filtered(
            lambda p: p.state not in ['done', 'cancel'])
        quant = self.env['stock.quant']
        for picking in pickings:
            picking.action_confirm()
            active_model = self._context.get('active_model')
            if active_model == 'sale.order.confirm_and_pay':
                wizard = self.env[active_model].browse(
                    self._context['active_id'])
                wizard.fill_lots(picking.move_ids)
            elif self.team_id.force_stock:
                picking.with_context(force_stock=True).action_assign()
                for move in picking.move_ids:
                    move.quantity_done = move.product_uom_qty
            else:
                for move in picking.move_ids:
                    available_qty = quant._get_available_quantity(
                        move.product_id, move.location_id)
                    if move.product_uom_qty > available_qty:
                        raise UserError(
                            _('%s units of the product %s are ordered but only '
                              '%s units in stock') % (
                                move.product_uom_qty, move.product_id.name,
                                available_qty))
                picking.action_assign()
                for move in picking.move_ids:
                    move.quantity_done = move.product_uom_qty
            picking.with_context(
                skip_sms=True, bypass_set_number_of_packages=True
            ).button_validate()
            if picking.state != 'done':
                raise UserError(_('Don\'t have enough stock for products'))
        return True

    def confirm_current_sale_session(self):
        self.ensure_one()
        self._check_sale_session_confirm_conditions()
        sales_team = self.env['crm.team'].search([
            ('member_ids', 'in', self.env.user.ids),
        ])
        if not sales_team:
            raise models.UserError(_(
                'You must be a member of a team to confirm with a sale '
                'session.'))
        session = self.env['sale.session'].get_current_sale_session(
            sales_team.id)
        if not session:
            raise models.UserError(_(
                'There is no open sale session for your team. '
                'Please create or open a sale session.'))
        self.write({
            'session_id': session.id,
            'team_id': session.team_id.id,
        })
        return self.with_context(open_wizard=True).action_confirm()

    def session_confirm_and_create_invoice(self):
        res = self.session_confirm()
        if res is not True:
            return res
        invoice_journal = (
            self.session_id.team_id.invoice_journal_ids
            and self.session_id.team_id.invoice_journal_ids[0] or False)
        if invoice_journal:
            self = self.with_context(default_journal_id=invoice_journal)
        invoice = self._create_invoices()
        if (not self.partner_id.vat
                and self.session_id.team_id.simplified_journal_id):
            invoice.journal_id = (
                self.session_id.team_id.simplified_journal_id.id)
        invoice.with_context(bypass_risk=True).action_post()
        return True

    def register_payment(self, vals):
        res = self.invoice_ids.action_register_payment()
        payment_wizard = self.env['account.payment.register'].with_context(
            **res['context']).create({
                'journal_id': vals['journal_id'].id,
                'amount': vals['amount'],
                'sale_session_id': self.session_id.id,
            })
        result = payment_wizard.with_context(
            payment_account_id=vals['journal_id'].default_account_id
        ).action_create_payments()
        payment = self.env['account.payment'].browse(result['res_id'])
        payment.sale_session_id = self.session_id.id
        payment.message_post_with_view(
            'mail.message_origin_link',
            values={'self': payment, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id)

    def session_pay(
            self, amount=0, payment_journal=False, payment_line_ids=False):
        res = self.session_confirm_and_create_invoice()
        if res is not True:
            return res
        if not payment_line_ids:
            self.register_payment({
                'journal_id': payment_journal,
                'amount': amount,
            })
            self.sale_session_payment_journal_ids = [
                (4, payment_journal.id)]
            return True
        for payment_line in payment_line_ids:
            self.register_payment({
                'journal_id': payment_line.journal_id,
                'amount': payment_line.amount,
            })
            self.sale_session_payment_journal_ids = [
                (4, payment_line.journal_id.id)]
        return True

    def open_confirm_and_pay(self):
        self.ensure_one()
        if not self.session_id:
            raise UserError(_('For confirm and paid must have a sale session.'))
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': self.id,
            'journal_id': (
                self.session_id.team_id.cash_payment_journal_id.id),
        })
        action = self.env.ref(
            'sale_session.sale_order_confirm_and_pay_action').read()[0]
        action['res_id'] = wizard.id
        return action
