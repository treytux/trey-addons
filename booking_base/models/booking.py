# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class Booking(models.Model):
    _name = 'booking'
    _description = 'Booking'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'date desc, name desc'
    _track = {
        'state': {
            'file.mt_file_open': lambda self, cr, uid, obj, ctx=None:
            obj.state == 'open',
            'file.mt_file_done': lambda self, cr, uid, obj, ctx=None:
            obj.state == 'done',
        },
    }

    @api.one
    @api.depends('booking_line')
    def _currency_id(self):
        if self.booking_line:
            for line in self.booking_line:
                if line.sell_currency_id:
                    self.currency_id = line.sell_currency_id
                    break

    @api.one
    @api.depends('booking_line')
    def _cost_currency_id(self):
        if self.booking_line:
            return self.booking_line[0].cost_currency_id
            # for line in self.booking_line:
            #     if line.cost_currency_id:
            #         self.cost_currency_id = line.cost_currency_id
            #         break

    name = fields.Char(
        string='Code',
        required=True,
        copy=False,
        index=True,
        select=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('paid', 'Paid'),
         ('done', 'Done'),
         ('canceled', 'Canceled'),
         ('cancelcus', 'Cancel by Customer')],
        default='draft',
        string='State',
        index=True,
        copy=False,
        track_visibility='onchange')
    date = fields.Datetime(
        string='Date',
        required=True,
        index=True)
    date_limit = fields.Datetime(
        string='Date Limit')
    date_init = fields.Datetime(
        string='Date init')
    date_modify = fields.Datetime(
        string='Last Modified')
    date_cancel = fields.Datetime(
        string='Cancel Date')
    date_end = fields.Datetime(
        string='End Travel')
    description = fields.Char(
        string='Description',
        size=250)
    channel = fields.Char(
        string='Channel')
    remarks = fields.Text(
        string='Notes')
    in_remarks = fields.Text(
        string='Internal Notes')
    in_financial_note = fields.Text(
        string='Financial Notes')
    agency_id = fields.Many2one(
        comodel_name='res.partner',
        string='Agency')
    booking_line = fields.One2many(
        comodel_name='booking.line',
        inverse_name='booking_id',
        string='Booking Line')
    invoices = fields.One2many(
        comodel_name='account.invoice',
        inverse_name='booking_id',
        string='Invoice Reference',
        readonly=True)
    holder_id = fields.Many2one(
        comodel_name='booking.holder',
        string='Holder')
    amount_pending = fields.Float(
        string='Pending')
    amount_cost_gross = fields.Float(
        string='Gross Cost',
        track_visibility='onchange')
    amount_cost_net = fields.Float(
        string='Net Cost',
        track_visibility='onchange')
    amount_commission = fields.Float(
        string='Commission',
        track_visibility='onchange')
    amount_selling = fields.Float(
        string='Total',
        track_visibility='onchange')
    invoiced = fields.Boolean(
        string='Invoiced',
        track_visibility='always')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_currency_id',
        store=True)
    cost_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Cost Currency',
        compute='_cost_currency_id',
        store=True)
