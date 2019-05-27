# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import base64
import logging
_log = logging.getLogger(__name__)


try:
    import xlrd
except ImportError:
    _log.debug(_(
        'Library xlrd not installed. Install it with: sudo pip install xlrd'))
    xlrd = None


class WizardCancelJuniperBooking(models.TransientModel):
    _name = 'wizard.cancel.juniper.booking'

    name = fields.Char(
        string='name')
    ffile = fields.Binary(
        string='File xml',
        filters='*.xml',
        required=True)

    @api.multi
    def cancel_juniper_booking(self, ffile):
        if not self.ffile:
            return False
        book = xlrd.open_workbook(file_contents=ffile)
        sheet_1 = book.sheet_by_index(0)
        booking_obj = self.env['booking']
        for rx in range(sheet_1.nrows):
            juniper_booking_locator = sheet_1.cell_value(rowx=rx, colx=0)
            booking = booking_obj.search([
                ('name', '=', juniper_booking_locator),
                ('juniper_id', '!=', 0)])
            if not booking or booking.methabook_id != 0:
                continue
            booking.state = 'canceled'
            self.env.cr.commit()

    @api.multi
    def button_cancel_juniper_booking(self):
        active_id = self.env.context.get('active_id', False)
        if not active_id:
            return
        if self.ffile:
            try:
                ffile = base64.decodestring(self.ffile)
                self.cancel_juniper_booking(ffile)
            except Exception as e:
                raise exceptions.Warning(
                    _('It has occurred following error: %s.' % e))
