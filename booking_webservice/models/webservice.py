# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class BookingWebservice(models.Model):
    _name = 'booking.webservice'
    _description = "Boookings WebService"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.one
    def _buffer_count(self):
        count = 0
        count += self.env['booking.webservice.buffer'].search_count([
            ('webservice_id', '=', self.id),
            ('state', '!=', 'done')])
        self.total_buffer = count

    name = fields.Char(
        string="Name",
        required=True)
    type = fields.Selection(
        string="Type",
        selection=[('juniper', 'Juniper')],
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        default=(lambda self: self.env['res.company']._company_default_get(
            'booking.webservice')))
    url = fields.Char(
        string="Url",
        required=True,
        select=True)
    username = fields.Char(
        string="User Name",
        required=True,
        select=False)
    password = fields.Char(
        string="Password",
        required=True)
    jobs_ids = fields.One2many(
        comodel_name='booking.webservice.job',
        inverse_name='webservice_id',
        string="Log",
        required=False,
        track_visibility='onchange')
    buffer_ids = fields.One2many(
        comodel_name='booking.webservice.buffer',
        inverse_name='webservice_id',
        string="Booking Buffer",
        required=False)
    total_buffer = fields.Integer(
        string="Pending",
        compute='_buffer_count')


class BookingWebserviceJob(models.Model):
    _name = 'booking.webservice.job'
    _description = "Boookings WebService Job"
    _order = 'date desc'
    _rec_name = 'date'

    date = fields.Date(
        string="Date",
        required=True)
    amount_element = fields.Integer(
        string="Elements",
        required=False)
    webservice_id = fields.Many2one(
        comodel_name='booking.webservice',
        string="WebService",
        required=True,
        ondelete='cascade')
    object_model = fields.Char(
        string="Model",
        required=False)
    note = fields.Text(
        string="Notes",
        required=False)


class BookingWebserviceBuffer(models.Model):
    _name = 'booking.webservice.buffer'
    _description = "Booking WebService Buffer"
    _rec_name = 'date'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('error', 'Error')],
        default='draft',
        string="State",
        index=True,
        copy=False)
    date = fields.Datetime(
        string="Date",
        help="Create date of the booking system",
        required=True)
    data = fields.Text(
        string="Data",
        required=True)
    webservice_id = fields.Many2one(
        comodel_name='booking.webservice',
        string="WebService",
        required=True,
        ondelete='cascade',
        select=True)
    booking_code = fields.Char(
        string="Code",
        required=False,
        select=True)
    active = fields.Boolean(
        string="Active",
        index=True,
        default=True)
    note = fields.Text(
        string="Log",
        required=False)


class BookingWebserviceParnertCode(models.Model):
    _name = 'booking.webservice.partner.ref'
    _description = "Booking WebService Partner"

    webservice_id = fields.Many2one(
        comodel_name='booking.webservice',
        string="WebService",
        required=True,
        ondelete='cascade',
        select=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Partner",
        required=True,
        ondelete='cascade')
    ptype = fields.Selection(
        string='Type of Partner',
        selection=[
            ('customer', 'Customer'),
            ('supplier', 'Supplier')],
        required=True,
        default='customer')
    res_id = fields.Integer(
        string='Resource Id',
        required=True)
