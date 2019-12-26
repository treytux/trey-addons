# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _


class BookingAccountJournal(models.Model):
    _name = 'booking.journal'
    _description = 'Booking Journal'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        default=lambda s: s.env.user.company_id,
        required=False)
    currency_id = fields.Many2one(
        comodel_name='res.currency')
    invoice_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Invoice Journal",
        required=False)
    payment_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Payment Journal",
        required=False)
    default = fields.Boolean(
        string="Default")

    @api.one
    @api.constrains('default')
    def _check_is_default(self):
        default_ids = self.env['booking.journal'].search([(
            'default', '=', True)])
        if not default_ids:
            raise exceptions.Warning(
                _('Please select one currency has default configuration'))
        if len(default_ids) > 1:
            raise exceptions.Warning(
                _('Only one currency by default configuration'))
