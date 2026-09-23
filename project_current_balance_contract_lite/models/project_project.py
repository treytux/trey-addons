###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import _, api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    contract_lite_line_id = fields.Many2one(
        'contract_lite.line',
        string='Contract Line',
        domain='''[
            ("contract_id.partner_id", "=", partner_id),
            ("contract_id.active", "=", True),
            ("recurring_next_date", "!=", False),
        ]''',
    )
    contract_lite_balance = fields.Float(
        string='Contract Balance',
        compute='_compute_contract_lite_balance',
        store=True,
        help='Balance of hours available in the corresponding contract.',
    )
    renewal_period_lite = fields.Selection(
        selection=[
            ('dayly', _('Days')),
            ('weekly', _('Weeks')),
            ('monthly', _('Monthly')),
            ('quarterly', _('Quarterly')),
            ('four_monthly', _('Four-month periods')),
            ('semesterly', _('Semesterly')),
            ('yearly', _('Yearly')),
        ],
        compute='_compute_renewal_period_lite',
        store=True,
        help='The renewal period as defined in the contract line.',
    )
    pending_invoices = fields.Many2many(
        'account.move',
        string='Pending Invoices',
        compute='_compute_pending_invoices',
        help='List of unpaid or not cancelled invoices related to the '
        'contract line.',
    )
    has_pending_invoices = fields.Boolean(
        string='Has Pending Invoices',
        compute='_compute_pending_invoices',
        help='Indicates if the related project has pending invoices.',
    )
    pending_invoices_since = fields.Date(
        string='Pending Invoices Since',
        compute='_compute_pending_invoices',
        help='The date of the earliest pending invoice.',
    )

    @api.depends('contract_lite_line_id.quantity')
    def _compute_contract_lite_balance(self):
        for project in self:
            project.contract_lite_balance = (
                project.contract_lite_line_id.quantity
                if project.contract_lite_line_id else 0.0)

    @api.depends('contract_lite_line_id.recurring_rule_type')
    def _compute_renewal_period_lite(self):
        valid_rule_types = [
            'dayly',
            'weekly',
            'monthly',
            'quarterly',
            'four_monthly',
            'semesterly',
            'yearly',
        ]
        for project in self:
            rule_type = project.contract_lite_line_id.recurring_rule_type
            project.renewal_period_lite = (
                rule_type if rule_type in valid_rule_types else False
            ) if project.contract_lite_line_id else False

    def _get_start_date(self, renewal_period_lite):
        today = fields.Date.today()
        if renewal_period_lite == 'dayly':
            return today
        if renewal_period_lite == 'weekly':
            return today - timedelta(days=today.weekday())
        if renewal_period_lite == 'monthly':
            return today.replace(day=1)
        if renewal_period_lite == 'yearly':
            return today.replace(month=1, day=1)
        if renewal_period_lite == 'quarterly':
            first_month = 3 * ((today.month - 1) // 3) + 1
            return today.replace(month=first_month, day=1)
        if renewal_period_lite == 'four_monthly':
            first_month = 4 * ((today.month - 1) // 4) + 1
            return today.replace(month=first_month, day=1)
        if renewal_period_lite == 'semesterly':
            first_month = 6 * ((today.month - 1) // 6) + 1
            return today.replace(month=first_month, day=1)
        return False

    @api.depends('contract_lite_line_id')
    def _compute_pending_invoices(self):
        move_model = self.env['account.move'].sudo()
        has_mandate = 'mandate_id' in move_model._fields
        for project in self:
            if not project.contract_lite_line_id:
                project.pending_invoices = False
                project.has_pending_invoices = False
                project.pending_invoices_since = False
                continue
            if has_mandate:
                domain = [
                    ('payment_state', 'not in', ['in_payment', 'paid']),
                    ('mandate_id', '=', False),
                    ('invoice_line_ids.contract_lite_line_id', '=',
                     project.contract_lite_line_id.id),
                ]
            else:
                domain = [
                    ('payment_state', 'not in', ['in_payment', 'paid']),
                    ('invoice_line_ids.contract_lite_line_id', '=',
                     project.contract_lite_line_id.id),
                ]
            invoices = move_model.search(domain)
            today = fields.Date.context_today(project)
            invoice_dates = [
                invoice_date for invoice_date in invoices.mapped('invoice_date')
                if invoice_date
            ]
            pending_invoices_since = min(invoice_dates) if invoice_dates else False
            project.pending_invoices = invoices
            project.pending_invoices_since = pending_invoices_since
            project.has_pending_invoices = bool(invoices) and (
                not pending_invoices_since
                or pending_invoices_since <= today
            )

    @api.depends(
        'extra_balance',
        'extra_balance_date',
        'timesheet_ids.date',
        'timesheet_ids.unit_amount',
        'contract_lite_line_id',
        'contract_lite_line_id.quantity',
        'contract_lite_line_id.recurring_rule_type',
        'has_pending_invoices',
        'renewal_period_lite',
    )
    def _compute_current_balance(self):
        for project in self:
            if (
                not project.contract_lite_line_id
                or not project.renewal_period_lite
            ):
                project.current_balance = project._get_base_current_balance()
                continue
            balance = 0.0 if project.has_pending_invoices else (
                project.contract_lite_balance)
            start_date = project._get_start_date(project.renewal_period_lite)
            hours_logged = sum(
                project._get_balance_timesheets(start_date).mapped(
                    'unit_amount'))
            project.current_balance = balance - hours_logged
