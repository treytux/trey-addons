###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class ContractLiteContract(models.Model):
    _name = 'contract_lite.contract'
    _description = 'Contract'
    _order = 'id desc'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'portal.mixin',
    ]

    name = fields.Char(
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('closed', 'Closed'),
        ],
        default='draft',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    code = fields.Char(
        string='Reference',
        default='Service #MONTH_STR# #YEAR#',
        help='Tokens: #MONTH_INT#, #MONTH_STR#, #YEAR#',
    )
    line_ids = fields.One2many(
        comodel_name='contract_lite.line',
        inverse_name='contract_id',
        string='Lines',
    )
    invoice_count = fields.Integer(
        string='Invoices',
        compute='_compute_invoice_count',
    )
    recurring_next_date = fields.Date(
        string='Next invoice date',
        compute='_compute_portal_dates',
        store=True,
    )
    date_end = fields.Date(
        string='End date',
        compute='_compute_portal_dates',
        store=True,
    )
    line_count = fields.Integer(
        string='Line count',
        compute='_compute_line_count',
    )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for contract in self:
            contract.line_count = len(contract.line_ids)

    @api.depends(
        'line_ids', 'line_ids.recurring_next_date', 'line_ids.date_end')
    def _compute_portal_dates(self):
        for contract in self:
            next_dates = [
                line.recurring_next_date
                for line in contract.line_ids
                if line.recurring_next_date
                and (
                    not line.date_end
                    or line.date_end >= line.recurring_next_date)
            ]
            end_dates = [d for d in contract.line_ids.mapped('date_end') if d]
            contract.recurring_next_date = min(
                next_dates) if next_dates else False
            contract.date_end = max(end_dates) if end_dates else False

    def _compute_access_url(self):
        for contract in self:
            contract.access_url = '/my/contracts-lite/%s' % contract.id

    def _compute_invoice_count(self):
        Move = self.env['account.move']
        for contract in self:
            contract.invoice_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('contract_lite_contract_id', '=', contract.id),
            ])

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'account.action_move_out_invoice_type')
        action['domain'] = [
            ('move_type', '=', 'out_invoice'),
            ('contract_lite_contract_id', '=', self.id),
        ]
        action['context'] = dict(
            self.env.context,
            default_move_type='out_invoice',
            default_partner_id=self.partner_id.id,
            search_default_draft=0,
            search_default_posted=0,
        )
        return action

    def action_create_invoices_manual(self):
        moves = self.cron_create_invoices(
            contracts=self)
        action = self.env['ir.actions.actions']._for_xml_id(
            'account.action_move_out_invoice_type')
        action['domain'] = [('id', 'in', moves.ids)]
        return action

    def action_finish_contract(self):
        today = fields.Date.context_today(self)
        for contract in self:
            contract.line_ids.write({'date_end': today})
            contract.state = 'closed'
        return True

    def action_activate(self):
        for contract in self:
            if not contract.line_ids:
                raise UserError(
                    _('You cannot activate a contract without lines.'))
            contract.state = 'active'

    def action_set_draft(self):
        self.write({
            'state': 'draft',
        })

    def _month_str(self, d):
        self.ensure_one()
        try:
            return format_date(self.env, d, date_format='MMMM').capitalize()
        except Exception:
            return d.strftime('%B').capitalize()

    def _fmt_date(self, d):
        try:
            return format_date(self.env, d)
        except Exception:
            return fields.Date.to_string(d)

    def _replace_tokens(self, text, tokens):
        if not text:
            return ''
        result = text
        for key, value in tokens.items():
            result = re.sub(
                re.escape(key), value or '', result, flags=re.IGNORECASE)
        return result.strip()

    def render_invoice_ref(self, invoice_date):
        self.ensure_one()
        tokens = {
            '#MONTH_INT#': invoice_date.strftime('%m'),
            '#MONTH_STR#': self._month_str(invoice_date),
            '#YEAR#': str(invoice_date.year),
        }
        return self._replace_tokens(self.code, tokens)

    def render_line_description(self, template, date_start, date_end):
        self.ensure_one()
        tokens = {
            '#START#': self._fmt_date(date_start),
            '#END#': self._fmt_date(date_end),
            '#START_MONTH_INT#': date_start.strftime('%m'),
            '#START_MONTH_STR#': self._month_str(date_start),
            '#START_YEAR#': str(date_start.year),
            '#END_MONTH_INT#': date_end.strftime('%m'),
            '#END_MONTH_STR#': self._month_str(date_end),
            '#END_YEAR#': str(date_end.year),
        }
        return self._replace_tokens(template, tokens)

    def _get_contracts_to_invoice_domain(self):
        domain = [('state', '=', 'active')]
        return domain

    def cron_create_invoices(self, contracts=None, today=None):
        if today is None:
            today = fields.Date.context_today(self)
        contracts = (
            self.search(self._get_contracts_to_invoice_domain()) if
            not contracts else contracts)
        if not contracts:
            return self.env['account.move']
        lines = self.env['contract_lite.line'].search([
            ('contract_id', 'in', contracts.ids)] if contracts else [])
        lines = lines.filtered(
            lambda line: line.date_start
            and line.recurring_next_date
            and line.date_start <= today
            and line.recurring_next_date <= today
            and (
                not line.date_end or line.date_end >= line.recurring_next_date)
            and line.contract_id.state == 'active'
        )
        if not lines:
            return self.env['account.move']
        buckets = {}
        for line in lines:
            key = (
                line.company_id.id,
                line.partner_id.id,
                line.contract_id.id,
                line.recurring_next_date,
            )
            buckets.setdefault(key, self.env['contract_lite.line'])
            buckets[key] |= line
        move_obj = self.env['account.move']
        company_obj = self.env['res.company']
        partner_obj = self.env['res.partner']
        contract_obj = self.env['contract_lite.contract']
        for (
            company_id,
            partner_id,
            contract_id,
            invoice_date,
        ), bucket_lines in buckets.items():
            company = company_obj.browse(company_id)
            partner = partner_obj.browse(partner_id)
            contract = contract_obj.browse(contract_id)
            journal = self.env['account.journal'].with_company(company).search(
                [('type', '=', 'sale'), ('company_id', '=', company.id)],
                limit=1,
            )
            invoice_lines = []
            for line in bucket_lines:
                analytic_distribution = {}
                if line.analytic_account_id:
                    analytic_distribution = {str(
                        line.analytic_account_id.id): 100}
                invoice_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.render_invoice_line_description(
                        line.recurring_next_date),
                    'quantity': line.quantity,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': line.price_unit or 0.0,
                    'discount': line.discount or 0.0,
                    'analytic_distribution': analytic_distribution,
                    'contract_lite_line_id': line.id,
                }))
            move_vals = {
                'move_type': 'out_invoice',
                'company_id': company.id,
                'partner_id': partner.id,
                'invoice_date': invoice_date,
                'ref': contract.render_invoice_ref(invoice_date),
                'invoice_origin': contract.name,
                'contract_lite_contract_id': contract.id,
                'invoice_payment_term_id': (
                    partner.property_payment_term_id.id or False),
                'fiscal_position_id': (
                    partner.property_account_position_id.id or False),
                'partner_bank_id': partner.bank_ids[:1].id or False,
                'journal_id': journal.id or False,
                'invoice_line_ids': invoice_lines,
            }
            move = move_obj.with_company(company).create(
                move_vals)
            move.user_id = partner.commercial_partner_id.user_id.id
            move_obj |= move
            for line in bucket_lines:
                line.recurring_next_date = line.compute_next_date(
                    line.recurring_next_date)
        return move_obj
