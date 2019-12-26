# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
import base64
import logging
_log = logging.getLogger(__name__)
try:
    from xlrd import open_workbook
except ImportError:
    _log.debug(_(
        'Library xlrd not installed. Install it with: sudo pip install xlrd'))


class WizardImportBookingUpdate(models.TransientModel):
    _name = 'wizard.import.booking.import'

    name = fields.Char(
        string='Empty')
    ffile = fields.Binary(
        string='File csv',
        filters='*.xls',
        required=True)
    stype = fields.Selection(
        string="Type",
        selection=[
            ('create', 'Create Date'),
            ('end', 'End Service Date'),
            ('booking_excel', 'Export booking with excel'),
            ('booking', 'Booking')],
        required=False,
        default='booking',
        help='Select type of booking selection or Create date or End of '
             'Service date')
    init_date = fields.Date(
        string="Date Init",
        help='Booking creation date from')
    end_date = fields.Date(
        string="Date End",
        help='Booking creation date to')
    wiz_booking_code = fields.Char(
        string="Code")

    @api.multi
    def get_locator_list_from_file(self):
        if not self.ffile:
            return False
        book = open_workbook(file_contents=base64.decodestring(self.ffile))
        sh = book.sheet_by_index(0)
        return [str(sh.cell_value(rowx=rx, colx=0)) for rx in range(sh.nrows)]

    @api.multi
    def button_ok(self):
        """
        ----------------------------------------------------------------------
        Desde el objeto webservice se habilita un boton para poder lanzar
        una la actualización/creación de reservas mediante un archivo excel.
        Se comprobara siempre si las reservas existen en el sistema por la
        funcion general de sincronizacion.
        ----------------------------------------------------------------------
        :return: ids
        ----------------------------------------------------------------------
        """
        active_id = self.env.context.get('active_id', False)
        if not active_id:
            return
        webservice_id = self.env['booking.webservice'].browse(active_id)
        if webservice_id.type == 'juniper':
            _log.info('=' * 79)
            _log.info('Starting Update Booking Type=ImportExcelManual')
            _log.info('=' * 79)
            for booking_code in self.get_locator_list_from_file():
                try:
                    _log.info('X' * 80)
                    _log.info(('booking_code', booking_code))
                    _log.info('X' * 80)
                    webservice_id.with_context(cron=False).update_bookings(
                        init_date=self.init_date, end_date=self.end_date,
                        stype='booking_Excel', wiz_booking_code=booking_code)
                except Exception:
                    continue
            _log.info('=' * 79)
            _log.info('Finish Update Booking Type=ImportExcelManual')
            _log.info('=' * 79)
