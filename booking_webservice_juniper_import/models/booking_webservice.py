# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import json
import logging
_log = logging.getLogger(__name__)
try:
    import xmltodict
except ImportError:
    _log.debug(_(
        'Library xlrd not installed. Install it with: sudo pip install xlrd'))


class BookingWebservice(models.Model):
    _inherit = 'booking.webservice'

    @api.multi
    def button_wizard_cancel_juniper_booking(self):
        view = self.env.ref('booking_webservice_juniper_import.'
                            'view_wizard_cancel_juniper_booking')
        return {
            # 'name': _('Manual Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.cancel.juniper.booking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def button_load_booking_from_buffer(self):
        if not self.type == 'juniper':
            raise exceptions.Warning(_('Webservice type must be Juniper.'))
        self.with_context(cron=False).update_bookings(False)

    @api.multi
    def button_wizard_manual_update(self):
        view = self.env.ref('booking_webservice_juniper_import.'
                            'view_wizard_manual_import_booking')
        return {
            # 'name': _('Manual Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.manual.import.booking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def button_wizard_assign_partner_account_ref(self):
        view = self.env.ref('booking_webservice_juniper_import.'
                            'view_wizard_assing_partner_account_ref')
        return {
            'name': _('Assing Partner account_ref'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.assing.partner.account.ref',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def booking_from_xml(self, file_xml):
        if not file_xml:
            return False
        x = xmltodict.parse(file_xml)
        lr = x['soap:Envelope']['soap:Body']['getBookingsResponse']
        if 'Bookings' not in lr['getBookingsResult']['wsResult']:
            raise exceptions.Warning(
                _('No bookings found !'),
                _('Try with another dates range or booking code'))
        return lr['getBookingsResult']['wsResult']['Bookings']['Booking']

    @api.one
    def find_travel_end(self, booking=None):
        """
        ----------------------------------------------------------------------
        Busca en las lineas, la fecha mas antigüa de fin de viaje
        :param booking: Objeto reserva
        ----------------------------------------------------------------------
        :return: Fecha en formato texto
        ----------------------------------------------------------------------
        """
        dates = []
        if type(booking['Lines']['Line']) == list:
            for line in booking['Lines']['Line']:
                dates.append(fields.Datetime.from_string(
                    line['EndTravelDate'].replace('T', ' ')))
        else:
            dates.append(fields.Datetime.from_string(
                booking['Lines']['Line']['EndTravelDate'].replace('T', ' ')))
        dates.sort(reverse=True)
        return fields.Datetime.to_string(dates[0] or False)

    @api.one
    def booking_to_processed(self):
        booking_buffer_ids = self.env['booking.webservice.buffer'].search([
            ('webservice_id', '=', self.id),
            ('state', '!=', 'done'),
            ('active', '=', True)])
        return booking_buffer_ids

    @api.multi
    def update_bookings(self, file_xml):
        """
        ----------------------------------------------------------------------
        Proceso principal de sincronizacion.
        ----------------------------------------------------------------------
        :return: None
        ----------------------------------------------------------------------
        """
        for webservice in self:
            if webservice.type == 'juniper':
                booking_ids = self.booking_to_processed()
                _log.info('X' * 80)
                _log.info(('booking_ids', booking_ids))
                _log.info('X' * 80)
                for booking in booking_ids[0]:
                    # Cada "booking" es un webservice.booking.buffer!
                    try:
                        self.update_juniper_bookings(
                            booking=booking, webservice=webservice.id)
                        booking.state = 'done'
                        booking.active = False
                    except Exception as inst:
                        booking.state = 'error'
                        booking.note = '<br/>%s' % inst.args[0]
                        # _log.info('Create booking in system error, '
                        #           'cache id:%s' % booking.id)
                        # _log.info('=' * 79)
                        pass
                jbookings = self.booking_from_xml(file_xml)
                if jbookings:
                    if type(jbookings) != list:
                        jbookings = [jbookings]
                    for jbooking in jbookings:
                        # ¿Esta la reserva creada como reserva?
                        if jbooking['@BookingCode'] in ['9ZW5PC']:
                            _log.info('X' * 80)
                            _log.info((
                                'booking & Status', jbooking['@BookingCode'],
                                jbooking['@Status']))
                            _log.info('X' * 80)

                        if self.env['booking'].search(
                                [('juniper_id', '=', jbooking['@Id'])]):
                            _log.info(
                                'Booking in system JuniperId:%s' % jbooking[
                                    '@Id'])
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
                                'juniper_date': (
                                    fields.Datetime.from_string(
                                        jbooking['@BookingDate'].replace(
                                            'T', ' '))),
                                'juniper_last_update': (
                                    fields.Datetime.from_string(
                                        jbooking['@LastModifiedDate'].replace(
                                            'T', ' '))),
                                'juniper_end_service': (
                                    self.find_travel_end(jbooking))}
                            # _log.info('Create booking in buffer, code:%s' %
                            #           jbooking['@BookingCode'])
                            self.env['booking.webservice.buffer'].create(
                                values)
                # Tras update volvemos a seleccionar las reservas en cache a
                #  procesar pero las mandamos a la funcion de creacion
                booking_ids = self.booking_to_processed()
                note = []
                is_error = False
                for booking in booking_ids[0]:
                    # Cada "booking" es un webservice.booking.buffer!
                    try:
                        self.update_juniper_bookings(
                            booking=booking, webservice=webservice.id)
                        booking.state = 'done'
                        booking.active = False
                    except Exception as inst:
                        booking.state = 'error'
                        booking.note = '<br/>%s' % inst.args[0]
                        _log.info(inst.args)
                        note.append(inst.args[0])
                        _log.info('Create booking in system error, '
                                  'cache id:%s' % booking.id)
                        _log.info('=' * 79)
                        is_error = True
                        pass
                if jbookings:
                    data_log = {
                        'date': fields.Date.from_string(fields.Date.today()),
                        'amount_element': len(jbookings),
                        'webservice_id': webservice.id,
                        'object_model': 'Booking',
                        'note': note}
                    self.env['booking.webservice.job'].create(data_log)
                if is_error:
                    body = _(r'Update buffer booking with errors:<br\/\>')
                    body += '<br/>'.join(note)
                    self.message_post(body=body)

    @api.one
    def update_juniper_bookings(self, booking=None, webservice=None):
        """
        ----------------------------------------------------------------------
        Creacion del objeto reserva en el sistema a partir del buffer y el
        campo data donde se almacenan los datos de la reserva en format json
        ----------------------------------------------------------------------
        :param booking:     Objeto reserva en el buffer
        :return:    True or False
        ----------------------------------------------------------------------
        """
        jbooking = json.loads(booking.data, encoding='utf-8')
        # _log.info('=' * 79)
        # _log.info('Create booking process code:%s' % jbooking[
        #     '@BookingCode'])
        # Preparamos los datos del titular
        fullname = jbooking['Holder']['NameHolder']
        fullname += ',' + jbooking['Holder']['LastName']
        holder_values = {
            'name': fullname,
            'lang': jbooking['Holder']['Nacionalidad'],
            'document_type': jbooking['Holder']['TipoDocumento'],
            'document_number': jbooking['Holder']['Dni'],
            'address': jbooking['Holder']['Address'],
            'country': jbooking['Holder']['Country'],
            'phone1': jbooking['Holder']['Phone1'],
            'phone2': jbooking['Holder']['Phone2'],
            'email': jbooking['Holder']['Email'],
            'nationality': jbooking['Holder']['Nacionalidad']}
        holder = self.env['booking.holder'].create(holder_values)
        if type(jbooking['Lines']['Line']) == list:
            jlines = jbooking['Lines']['Line']
        else:
            jlines = [jbooking['Lines']['Line']]
        line_values = []
        for jline in jlines:
            # Buscar el proveedor de la reserva
            supplier_id = self.create_supplier(jline=jline)
            if supplier_id:
                # Comprobar si existe la zona, si no la creamos
                zone_id = self.create_zone(jline=jline)
                # Preparamos los datos de la linea de reserva
                cost_currency_id = self.env['res.currency'].search([
                    ('name', '=', jline['CostCurrency'])])
                sell_currency_id = self.env['res.currency'].search([
                    ('name', '=', jline['SellCurrency'])])
                canceled = False
                if jline['@LineCancelled'] == "True":
                    canceled = True
                values = {
                    'name': jline['ServiceName'],
                    'booking_id': booking.id,
                    'juniper_id': jline['@IdBookLine'],
                    'supplier_id': supplier_id,
                    'ex_reference': jline['@Externalreference'],
                    'selling_price': jline['SellingPrice'],
                    'commission': jline['Commission'],
                    'per_commission': jline['PerCommission'],
                    'cost_net': jline['CostBaseLine'],
                    'pricecommission': jline['ComissionAmount'],
                    'amount_untaxed': jline['BasePriceWithOutTax'],
                    'amount': jline['BasePrice'],
                    'amount_cancel': jline['CancellationFees'],
                    'cost_change_factor': jline['CostChangeFactor'],
                    'base_change_factor': jline['BaseChangeFactor'],
                    'cost_currency_id': cost_currency_id.id or False,
                    'sell_currency_id': sell_currency_id.id or False,
                    'date_init': fields.Date.from_string(
                        jline['BeginTravelDate'].replace('T', ' ')),
                    'date_end': fields.Date.from_string(
                        jline['EndTravelDate'].replace('T', ' ')),
                    'date': fields.Date.from_string(
                        jline['@LineDate'].replace('T', ' ')),
                    'zone_id': zone_id,
                    'canceled': canceled}
                line_values.append((0, 0, values))
            else:
                msg = 'Create Supplier error booking: %s, Supplier: %s, ' % (
                    jbooking['@BookingCode'],
                    jline['Supplier']['SupplierName'])
                msg_1 = 'Supplier account in Juniper: %s' % (
                    jline['ProviderAccount'])
                raise Exception(msg + msg_1)
        customer_id = self.create_customer(jbooking=jbooking)
        if not customer_id:
            msg = 'Create Customer error booking: %s, Customer: %s, ' % (
                jbooking['@BookingCode'], jbooking['Customer']['Name'])
            msg_1 = 'Customer account in Juniper: %s' % (
                    jbooking['Customer'].get('ClientAccount', False))
            raise Exception(msg + msg_1)
        if jbooking['@Status'] == 'OK':
            state = 'paid'
        elif jbooking['@Status'] == 'Pag':
            state = 'paid'
        elif jbooking['@Status'] == 'CaC':
            state = 'cancelcus'
        elif jbooking['@Status'] == 'Con':
            state = 'confirmed'
        else:
            state = 'draft'
        header_values = {
            'name': jbooking['@BookingCode'],
            'date': fields.Date.from_string(
                jbooking['@BookingDate'].replace('T', ' ')),
            'date_modify': fields.Date.from_string(
                jbooking['@LastModifiedDate'].replace('T', ' ')),
            'date_init': line_values[0][2]['date_init'],
            'agency_id': customer_id,
            'holder_id': holder.id,
            'description': jbooking['Description'],
            'remarks': jbooking['Remarks'],
            'in_remarks': jbooking['InRemarks'],
            'in_financial_note': jbooking['FinancialNotes'],
            'amount_pending': jbooking['OutStandingAmount'],
            'amount_cost_gross': jbooking['Cost'],
            'amount_commission': jbooking['Commission'],
            'amount_selling': jbooking['SellingPrice'],
            'channel': jbooking['@Channel'],
            'juniper_id': jbooking['@Id'],
            'juniper_state': jbooking['@Status'],
            'state': state,
            'date_end': booking.juniper_end_service,
            'booking_line': line_values}
        if self.env['booking'].search([('juniper_id', '=', jbooking['@Id'])]):
            _log.warning('Booking already in the system: %s' % header_values)
        else:
            booking = self.env['booking'].create(header_values)
            # _log.info('Create booking id:%s code:%s' % (
            #     booking.id, jbooking['@BookingCode']))
            # _log.info('=' * 79)

    @api.model
    def create_customer(self, jbooking=None, code=None, webservice=None):
        account_ref = jbooking['Customer'].get('ClientAccount', False)
        if not account_ref:
            # Al buffer
            return None
        else:
            customers = self.get_partner(account_ref, 'customer')
            customers = customers.get('partner')
            if not customers:
                # Al buffer
                return None
            return customers and customers[0].id or None

    def get_partner(self, partner_account, ttype):
        def _get_customer(partner_account):
            my_partners = self.env['res.partner'].search([
                ('customer_account_ref', '=', partner_account)])
            return my_partners

        def _get_supplier(partner_account):
            my_partners = self.env['res.partner'].search([
                ('supplier_account_ref', '=', partner_account)])
            return my_partners

        if ttype == 'customer':
            my_partners = _get_customer(partner_account)
            if not my_partners:
                my_partners = _get_supplier(partner_account)
                if my_partners and my_partners[0]:
                    my_partners[0].customer_account_ref = partner_account
                    my_partners[0].customer = True
                    self.env.cr.commit()
        else:
            my_partners = _get_supplier(partner_account)
            if not my_partners:
                my_partners = _get_customer(partner_account)
                if my_partners and my_partners[0]:
                    my_partners[0].supplier_account_ref = (
                        partner_account)
                    my_partners[0].supplier = True
                    self.env.cr.commit()
        return {'partner': my_partners and my_partners[0] or None}

    @api.model
    def create_supplier(self, jline=None):
        supplier_account = jline.get('ProviderAccount', False)
        if not supplier_account:
            # al buffer
            return None
        else:
            suppliers = self.get_partner(supplier_account, 'supplier')
            suppliers = suppliers.get('partner')
            if not suppliers:
                # Al buffer
                return None
            return suppliers and suppliers[0].id or None

    @api.model
    def create_zone(self, jline=None, code=None):
        booking_zone_obj = self.env['booking.zone']
        zone_id = jline['Zone']['@Id']
        zone = booking_zone_obj.search([('juniper_id', '=', zone_id)])
        if not zone:
            if zone_id and jline['Zone']['description']:
                values = {
                    'name': jline['Zone']['description'],
                    'province': (
                        jline['Zone'] and jline['Zone']['state'] or False),
                    'country': jline['Zone']['country'],
                    'juniper_id': zone_id}
                zone = booking_zone_obj.create(values)
                return zone.id
            else:
                return None
        return zone.id
