# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class WizardManualUpdate(models.TransientModel):
    _name = 'wizard.booking.manual'
    _description = 'Wizard Booking Manual Update'

    stype = fields.Selection(
        string="Type",
        selection=[
            ('create', 'Create Date'),
            ('end', 'End Service Date'),
            ('booking', 'Booking')],
        required=False,
        default='create',
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

    @api.one
    def button_ok(self):
        """
        ----------------------------------------------------------------------
        Desde el objeto webservice se habilita un boton para poder lanzar
        una sincronizacion inicial desde una fecha en concreto. Esto es solo a
        nivel de consulta en juniper para el arranque inicial, se comprobara
        siempre si las reservas existen en el sistema por la funcion general de
        sincronizacion
        ----------------------------------------------------------------------
        :return: ids
        ----------------------------------------------------------------------
        """
        active_id = self.env.context.get('active_id', False)
        if active_id:
            webservice_id = self.env['booking.webservice'].browse(active_id)
            if webservice_id.type == 'juniper':
                _log.info('=' * 79)
                _log.info('Starting Update Booking Type=manual')
                _log.info('=' * 79)
                webservice_id.with_context(cron=False).update_bookings(
                    init_date=self.init_date, end_date=self.end_date,
                    stype=self.stype, wiz_booking_code=self.wiz_booking_code)
                _log.info('=' * 79)
                _log.info('Finish Update Booking Type=manual')
                _log.info('=' * 79)
