# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
from openerp.addons.booking_webservice_juniper.models import juniper
from datetime import timedelta
import json
import logging
_log = logging.getLogger(__name__)


class BookingWebservice(models.Model):
    _inherit = 'booking.webservice'

    @api.multi
    def update_bookings(self, init_date=None, end_date=None, stype=None,
                        wiz_booking_code=None):
        """
        ----------------------------------------------------------------------
        Proceso principal de sincronizacion.Si en el context se recibe el
        campo init_date, se hace la sincronizacion desde init_date hasta hoy.
        ----------------------------------------------------------------------
        :return: None
        ----------------------------------------------------------------------
        """
        # Instanciar la Clase Juniper para las conexiones
        juniper_instance = juniper.Juniper(
            url=self.url, user=self.username, password=self.password)
        # Comprobar tipo de webservice para lanzar un proceso por tipo
        for webservice in self:
            if webservice.type == 'juniper':
                # Trae los booking del Buffer
                # booking_ids = self.booking_to_processed()
                if stype == 'booking_Excel':
                    # Update json de reservas en cache para procesar
                    booking_ids = self.booking_to_processed_no_limit()
                else:
                    # Update json de reservas en cache para procesar Con FECHA
                    booking_ids = self.booking_to_processed()
                if booking_ids and booking_ids[0]:
                    for booking in booking_ids[0]:
                        # Cada "booking" es un webservice.booking.buffer!
                        try:
                            self.update_juniper_bookings(
                                booking=booking, webservice=webservice.id)
                            booking.state = 'done'
                            booking.active = False
                        except Exception as inst:
                            booking.state = 'error'
                            args = (isinstance(inst.args, list) and
                                    inst.args[0] or inst.args[0])
                            booking.note = '<br/>%s' % str(args)
                            _log.info('Create booking in system error, '
                                      'cache id:%s' % booking.id)
                            _log.info('=' * 79)
                            pass
                # ****************************************
                #  AQUI PROCESAMOS LAS RESERVAS NUEVAS
                # ****************************************
                # Si es manual desde init_fecha
                if stype:
                    if stype == 'create':
                        # LLamada al webservice por fecha de creacion
                        dt2 = init_date.replace('-', '')
                        dt1 = end_date.replace('-', '')
                        jbookings = juniper_instance.booking(
                            BookingDateFrom=dt2,
                            BookingDateTo=dt1,
                            ExportMode='C',
                            ManualUpdate=True)
                    elif stype == 'end':
                        dt2 = init_date.replace('-', '')
                        dt1 = end_date.replace('-', '')
                        # Llamada al webservice por fecha de finalizacion
                        jbookings = juniper_instance.booking(
                            BeginTravelDate=dt2,
                            EndTravelDate=dt1,
                            ExportMode='C',
                            ManualUpdate=True)
                    elif stype == 'booking':
                        jbookings = juniper_instance.booking(
                            BookingCode=wiz_booking_code,
                            ExportMode='C',
                            ManualUpdate=True)
                    else:
                        jbookings = juniper_instance.booking_solole(
                            BookingCode=wiz_booking_code,
                            ExportMode='C',
                            ManualUpdate=True)
                else:
                    # Si es automatico desde ayer a hoy por fecha de creacion
                    dt = (
                        fields.Date.from_string(fields.Date.today()) -
                        timedelta(days=1))
                    dt2 = (fields.Date.to_string(dt)).replace('-', '')
                    dt1 = fields.Date.today().replace('-', '')
                    jbookings = juniper_instance.booking(
                        BookingDateFrom=dt2,
                        BookingDateTo=dt1,
                        ExportMode='C')
                # Aqui recupero las reservas para la fecha de hoy, ademas
                # escribo el log para saber que ha leido el sistema .
                if jbookings == ['False']:
                    raise exceptions.Warning(_('Connection Error'))
                if type(jbookings) != list:
                    jbookings = [jbookings]
                for jbooking in jbookings:
                    # ¿Esta la reserva creada como reserva?
                    booking_id = jbooking['@Id']
                    if self.env['booking'].search(
                            [('juniper_id', '=', booking_id)]):
                        _log.info(
                            'Booking in system JuniperId:%s' % booking_id)
                        continue
                    # ¿Esta la reserva en el buffer?
                    if self.env['booking.webservice.buffer'].search(
                            [('juniper_id', '=', jbooking['@Id'])]):
                        continue
                    # ¿Reserva cancelada por cliente sin coste?
                    if jbooking['@Status'] == 'CaC' and \
                       jbooking['SellingPrice'] == "0.00":
                        continue
                    # ¿Reserva con estado distinto a Cancelada o PreOrden?
                    if jbooking['@Status'] not in ('Can', 'Pre'):
                        jsonfile = json.dumps(
                            jbooking, indent=4, encoding='utf-8',
                            ensure_ascii=True, default=dict)
                        values = {
                            'date': fields.Date.today(),
                            'data': jsonfile,
                            'webservice_id': self.id,
                            'juniper_id': jbooking['@Id'],
                            'booking_code': jbooking['@BookingCode'],
                            'juniper_date': fields.Datetime.from_string(
                                jbooking['@BookingDate'].replace('T', ' ')),
                            'juniper_last_update': fields.Datetime.from_string(
                                jbooking['@LastModifiedDate'].replace(
                                    'T', ' ')),
                            'juniper_end_service': (
                                self.find_travel_end(jbooking))}
                        _log.info('Create booking in buffer, code:%s' %
                                  jbooking['@BookingCode'])
                        self.env['booking.webservice.buffer'].create(values)
                        self.env.cr.commit()
                if stype == 'booking_Excel':
                    # Update json de reservas en cache para procesar
                    pre_bookings_ids = self.booking_to_processed_no_limit()
                    booking_ws_buffer_list = pre_bookings_ids
                else:
                    # Update json de reservas en cache para procesar Con FECHA
                    # Tras update volvemos a seleccionar las reservas en cache
                    # a procesar pero las mandamos a la funcion de creacion
                    pre_bookings_ids = self.booking_to_processed()
                    for booking in pre_bookings_ids[0]:
                        self.update_json_booking(booking)
                    pre_bookings_ids = self.booking_to_processed()
                    booking_ws_buffer_list = booking_ids[0]
                note = []
                is_error = False
                for booking in booking_ws_buffer_list:
                    # Cada "booking" es un webservice.booking.buffer!
                    try:
                        self.update_juniper_bookings(
                            booking=booking, webservice=webservice.id)
                        note.append(booking.booking_code)
                        booking.state = 'done'
                        booking.active = False
                    except Exception as inst:
                        booking.state = 'error'
                        args = (isinstance(inst.args, list) and
                                inst.args[0] or inst.args[0])
                        booking.note = '<br/>%s' % str(args)
                        error_msg = ('Create booking in system error, '
                                     'cache id:%s' % booking.id)
                        _log.info(inst.args)
                        note.append('%s, %s' % (error_msg, args))
                        _log.info(error_msg)
                        _log.info('=' * 79)
                        is_error = True
                        pass
                data_log = {
                    'date': fields.Date.from_string(fields.Date.today()),
                    'amount_element': len(jbookings),
                    'webservice_id': webservice.id,
                    'object_model': 'Booking',
                    'note': note}
                self.env['booking.webservice.job'].create(data_log)
                if is_error:
                    body = _(r'Update buffer booking with errors:<br\/\>')
                    _log.info('X' * 80)
                    _log.info(('note', note))
                    _log.info('X' * 80)
                    if note:
                        body += str(note)
                    self.message_post(body=body)

    @api.one
    def booking_to_processed_no_limit(self):
        """
        ----------------------------------------------------------------------
        Selecciona del buffer las reservar que esten sin procesar, activas y
        cuya fecha fin de servicio sea anterior al dia de hoy.
        ----------------------------------------------------------------------
        :return: ids
        ----------------------------------------------------------------------
        """
        # Seleccionar reservas activas y sin procesar y las devuelve
        booking_buffer_ids = self.env['booking.webservice.buffer'].search([
            ('webservice_id', '=', self.id),
            ('state', '!=', 'done'),
            ('active', '=', True)])
        return booking_buffer_ids

    @api.multi
    def button_wizard_import_update(self):
        view = self.env.ref(
            'booking_webservice_juniper_end.view_wizard_import_update')
        return {
            'name': _('Export excel to Update bookings'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.import.booking.import',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }
