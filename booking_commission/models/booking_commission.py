# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, exceptions, fields, models, _


class BookingCommission(models.Model):
    _name = "booking.commission"
    _description = "Commission in bookings"

    @api.model
    def _get_default_company_id(self):
        company_obj = self.env['res.company']
        return company_obj.browse(
            company_obj._company_default_get('booking.commission'))

    name = fields.Char('Name', required=True)
    commission_type = fields.Selection(
        selection=[("fixed", "Fixed percentage"),
                   ("section", "By sections")],
        string="Type",
        required=True,
        default="fixed")
    fix_qty = fields.Float(
        string="Fixed percentage")
    sections = fields.One2many(
        comodel_name="booking.commission.section",
        inverse_name="commission")
    active = fields.Boolean(
        default=True)
    invoice_state = fields.Selection(
        selection=[('open', 'Invoice Based'), ('paid', 'Payment Based')],
        string='Invoice Status',
        required=True,
        default='open')
    amount_base_type = fields.Selection(
        selection=[('gross_amount', 'Gross Amount'),
                   ('net_amount', 'Net Amount')],
        string='Base',
        required=True,
        default='gross_amount')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=_get_default_company_id)

    @api.multi
    def calculate_section(self, base):
        self.ensure_one()
        for section in self.sections:
            if section.amount_from <= base <= section.amount_to:
                return base * section.percent / 100.0
        return 0.0


class SaleCommissionSection(models.Model):
    _name = "booking.commission.section"
    _description = "Commission section"

    commission = fields.Many2one(
        "booking.commission",
        string="Commission")
    amount_from = fields.Float(
        string="From")
    amount_to = fields.Float(
        string="To")
    percent = fields.Float(
        string="Percent",
        required=True)

    @api.one
    @api.constrains('amount_from', 'amount_to')
    def _check_amounts(self):
        if self.amount_to < self.amount_from:
            raise exceptions.ValidationError(
                _("The lower limit cannot be greater than upper one."))
