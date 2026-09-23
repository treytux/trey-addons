###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class ContractLiteSupplierContract(models.Model):
    _name = 'contract_lite_supplier.contract'
    _description = 'Supplier Contract'
    _order = 'id desc'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
    ]

    name = fields.Char(required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
    )
    active = fields.Boolean(default=True)
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
        default='Vendor service #MONTH_STR# #YEAR#',
        help='Tokens: #MONTH_INT#, #MONTH_STR#, #YEAR#',
    )
    line_ids = fields.One2many(
        comodel_name='contract_lite_supplier.line',
        inverse_name='contract_id',
        string='Lines',
    )
    bill_count = fields.Integer(
        string='Vendor bills',
        compute='_compute_bill_count',
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

    @api.depends('line_ids', 'line_ids.recurring_next_date',
                 'line_ids.date_end')
    def _compute_portal_dates(self):
        for contract in self:
            next_dates = [
                line.recurring_next_date
                for line in contract.line_ids
                if line.recurring_next_date
                and (
                    not line.date_end
                    or line.date_end >= line.recurring_next_date
                )
            ]
            end_dates = [d for d in contract.line_ids.mapped('date_end') if d]
            contract.recurring_next_date = (
                min(next_dates) if next_dates else False)
            contract.date_end = max(end_dates) if end_dates else False

    def _compute_bill_count(self):
        move_obj = self.env['account.move']
        for contract in self:
            contract.bill_count = move_obj.search_count([
                ('move_type', '=', 'in_invoice'),
                ('contract_lite_supplier_contract_id', '=', contract.id),
            ])

    def action_view_vendor_bills(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'account.action_move_in_invoice_type')
        action['domain'] = [
            ('move_type', '=', 'in_invoice'),
            ('contract_lite_supplier_contract_id', '=', self.id),
        ]
        action['context'] = dict(
            self.env.context,
            default_move_type='in_invoice',
            default_partner_id=self.partner_id.id,
            search_default_draft=0,
            search_default_posted=0,
        )
        return action

    def action_create_vendor_bills_manual(self):
        moves = self.cron_create_vendor_bills(contracts=self)
        action = self.env['ir.actions.actions']._for_xml_id(
            'account.action_move_in_invoice_type')
        action['domain'] = [('id', 'in', moves.ids)]
        return action

    def action_finish_contract(self):
        today = fields.Date.context_today(self)
        for contract in self:
            contract.line_ids.write({
                'date_end': today,
            })
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

    def _month_str(self, value_date):
        self.ensure_one()
        try:
            month = format_date(self.env, value_date, date_format='MMMM')
            return month.capitalize()
        except Exception:
            return value_date.strftime('%B').capitalize()

    def _fmt_date(self, value_date):
        try:
            return format_date(self.env, value_date)
        except Exception:
            return fields.Date.to_string(value_date)

    def _replace_tokens(self, text, tokens):
        if not text:
            return ''
        result = text
        for key, value in tokens.items():
            result = re.sub(
                re.escape(key), value or '', result, flags=re.IGNORECASE)
        return result.strip()

    def render_bill_ref(self, invoice_date):
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

    def _get_contracts_to_bill_domain(self):
        return [('state', '=', 'active')]

    def cron_create_vendor_bills(self, contracts=None, today=None):
        if today is None:
            today = fields.Date.context_today(self)
        contracts = (
            contracts
            or self.search(self._get_contracts_to_bill_domain())
        )
        if not contracts:
            return self.env['account.move']
        line_obj = self.env['contract_lite_supplier.line']
        lines = line_obj.search([('contract_id', 'in', contracts.ids)])
        lines = lines.filtered(
            lambda line: line.date_start
            and line.recurring_next_date
            and line.date_start <= today
            and line.recurring_next_date <= today
            and (
                not line.date_end
                or line.date_end >= line.recurring_next_date
            )
            and line.contract_id.state == 'active'
        )
        if not lines:
            return lines
        buckets = {}
        for line in lines:
            key = (
                line.company_id.id,
                line.partner_id.id,
                line.contract_id.id,
                line.recurring_next_date)
            buckets.setdefault(key, self.env['contract_lite_supplier.line'])
            buckets[key] |= line
        move_obj = self.env['account.move']
        company_obj = self.env['res.company']
        partner_obj = self.env['res.partner']
        contract_obj = self.env['contract_lite_supplier.contract']
        for (
            company_id,
            partner_id,
            contract_id,
            invoice_date
        ), bucket_lines in buckets.items():
            company = company_obj.browse(company_id)
            partner = partner_obj.browse(partner_id)
            contract = contract_obj.browse(contract_id)
            journal = self.env['account.journal'].with_company(company).search([
                ('type', '=', 'purchase'),
                ('company_id', '=', company.id),
            ], limit=1)
            line_values = []
            for line in bucket_lines:
                analytic_distribution = {}
                if line.analytic_account_id:
                    analytic_distribution = {
                        str(line.analytic_account_id.id): 100,
                    }
                line_values.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.render_invoice_line_description(
                        line.recurring_next_date),
                    'quantity': line.quantity,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': line.price_unit or 0.0,
                    'discount': line.discount or 0.0,
                    'analytic_distribution': analytic_distribution,
                    'contract_lite_supplier_line_id': line.id,
                }))
            move_vals = {
                'move_type': 'in_invoice',
                'company_id': company.id,
                'partner_id': partner.id,
                'invoice_date': invoice_date,
                'ref': contract.render_bill_ref(invoice_date),
                'invoice_origin': contract.name,
                'contract_lite_supplier_contract_id': contract.id,
                'invoice_payment_term_id': (
                    partner.property_supplier_payment_term_id.id or False),
                'fiscal_position_id': (
                    partner.property_account_position_id.id or False),
                'journal_id': journal.id or False,
                'invoice_line_ids': line_values,
            }
            move = move_obj.with_company(company).create(move_vals)
            move_obj |= move
            for line in bucket_lines:
                line.recurring_next_date = line.compute_next_date(
                    line.recurring_next_date)
        return move_obj
