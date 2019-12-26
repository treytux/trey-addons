# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _
from .juniper import Juniper
from datetime import timedelta
import json
import logging
_log = logging.getLogger(__name__)


class BookingWebservice(models.Model):
    _inherit = 'booking.webservice'

    @api.multi
    def button_wizard_manual_update(self):
        view = self.env.ref(
            'booking_webservice_juniper.view_wizard_manual_update')
        return {
            'name': _('Manual Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.booking.manual',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

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
    def update_json_booking(self, booking=None):
        """
        ----------------------------------------------------------------------
        Metodo para escribir la fecha de ultima actualizacion,
        fecha final de viaje y fichero json si la reserva se ha modificado
        ----------------------------------------------------------------------
        :param booking: Reserva a procesar
        :return: True si se ha modificado y procesado corectamente,
                 False si no se ha modificado
        ----------------------------------------------------------------------
        """
        # Instanciar la Clase Juniper para las conexiones
        juniper = Juniper(url=self.url,
                          user=self.username,
                          password=self.password)
        _log.info('Json update from juniper code: "%s"' % booking.booking_code)
        jbooking = juniper.booking(BookingCode=booking.booking_code)
        if jbooking:
            last_update = jbooking['@LastModifiedDate'].replace('T', ' ')
            if booking.juniper_last_update != last_update:
                booking.data = json.dumps(jbooking, indent=4, encoding='utf-8',
                                          ensure_ascii=True, default=dict)
                booking.juniper_last_update = last_update
                booking.juniper_end_service = self.find_travel_end(jbooking)[0]
                return True
        return False

    @api.one
    def booking_to_processed(self):
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
            ('active', '=', True),
            ('juniper_end_service', '<', fields.Date.today())])
        return booking_buffer_ids

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
        juniper = Juniper(url=self.url,
                          user=self.username,
                          password=self.password)
        # Comprobar tipo de webservice para lanzar un proceso por tipo
        for webservice in self:
            if webservice.type == 'juniper':
                # Seleccionamos reservas a procesar y comprobamos si han
                # sufrido cambios mediante la fecha de actualizacion,
                # de ser asi, se actualiza el fichero json y los campos
                # last_update y EndTravelDate

                # pre_bookings_ids = self.booking_to_processed()
                # for booking in pre_bookings_ids[0]:
                #     self.update_json_booking(booking)

                # Tras la actualizacion volvemos a seleccionar las reservas
                # a procesar
                booking_ids = self.booking_to_processed()
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
                        jbookings = juniper.booking(
                            BookingDateFrom=dt2,
                            BookingDateTo=dt1,
                            ExportMode='C',
                            ManualUpdate=True)
                    elif stype == 'end':
                        dt2 = init_date.replace('-', '')
                        dt1 = end_date.replace('-', '')
                        # Llamada al webservice por fecha de finalizacion
                        jbookings = juniper.booking(
                            BeginTravelDate=dt2,
                            EndTravelDate=dt1,
                            ExportMode='C',
                            ManualUpdate=True)
                    else:
                        jbookings = juniper.booking(
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
                    jbookings = juniper.booking(
                        BookingDateFrom=dt2,
                        BookingDateTo=dt1,
                        ExportMode='C')
                # Aqui recupero las reservas para la fecha de hoy, ademas
                # escribo el log para saber que ha leido el sistema .
                if type(jbookings) != list:
                    jbookings = [jbookings]
                for jbooking in jbookings:
                    # ¿Esta la reserva creada como reserva?
                    if self.env['booking'].search(
                            [('juniper_id', '=', jbooking['@Id'])]):
                        _log.info('Booking in system JuniperId:%s' % jbooking[
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
                pre_bookings_ids = self.booking_to_processed()
                # Update json de reservas en cache para procesar
                for booking in pre_bookings_ids[0]:
                    self.update_json_booking(booking)
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

    @api.multi
    def run_booking_update(self, init_date=None, end_date=None, stype=None):
        # Update booking at the given frequence
        webservices = self.search([])
        juniper_webservice = webservices.filtered(
            lambda ws: ws.type == 'juniper')
        juniper_webservice.with_context(cron=True).update_bookings(
            init_date=init_date, end_date=end_date, stype=stype)

    @api.model
    def _run_booking_update(self, init_date=None, end_date=None, stype=None):
        _log.info('=' * 79)
        _log.info('Starting Update Bookings Type=Cron')
        _log.info('=' * 79)
        self.run_booking_update(
            init_date=init_date, end_date=end_date, stype=stype)
        _log.info('=' * 79)
        _log.info('End Update Boooking Type=Cron')
        _log.info('=' * 79)

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
        _log.info('=' * 79)
        _log.info('Create booking process code:%s' % jbooking[
            '@BookingCode'])
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
        # Comprobar si vienen una (instancia) o varias lineas (Lista)
        if type(jbooking['Lines']['Line']) == list:
            jlines = jbooking['Lines']['Line']
        else:
            jlines = [jbooking['Lines']['Line']]
        line_values = []
        for jline in jlines:
            # Buscar el proveedor de la reserva
            supplier_id = self.create_supplier(
                code=jbooking['@BookingCode'], webservice=webservice,
                jline=jline)
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
                raise Exception(
                    'Create Supplier error booking:%s, Supplier:%s' %
                    (jbooking['@BookingCode'],
                     jline['Supplier']['SupplierName']))
        # Creamos el cliente y comprobamos que esta ok
        customer_id = self.create_customer(
            jbooking=jbooking, webservice=webservice,
            code=jbooking['@BookingCode'])
        if not customer_id:
            _log.error(
                'Create Customer error booking:%s, Customer:%s' % (
                    jbooking['@BookingCode'],
                    jbooking['Customer']['Name']))
            raise Exception(
                'Create Customer error booking:%s, Customer:%s' %
                (jbooking['@BookingCode'], jbooking['Customer']['Name']))
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
            _log.info('Create booking id:%s code:%s' % (
                booking.id, jbooking['@BookingCode']))
            _log.info('=' * 79)

    @api.model
    def create_customer(self, jbooking=None, code=None, webservice=None):
        """
        ----------------------------------------------------------------------
        Buscamos el cliente en el sistema por su identificador y filtrando
        por tipo customer. De no encontrarlo, buscamos los partners por el
        campo juniper AccountRefNumber. Si encontramos un partner con ese
        dato, lo marcamos como cliente
        ----------------------------------------------------------------------
        :param
            jbooking: Objeto Reserva
            code: codigo de la reserva
        :return: id del partner
        ----------------------------------------------------------------------
        """
        juniper = Juniper(
            url=self.url,
            user=self.username,
            password=self.password)
        fiscal_position_id = self.env['account.fiscal.position'].search([
            ('name', 'ilike', 'Exempt')])
        code_obj = self.env['booking.webservice.partner.ref']
        # Cargo el cliente desde juniper para tener la referencia de cuenta
        jcustomer = juniper.customer(id=jbooking['Customer']['@Id'])
        # Comprobar si el campo cuenta de cliente viene rellena, de no ser
        # asi, se sale
        if not jcustomer['InvoicingDetails']['AccountRefNumber']:
            # _log.info('AccountRefNumber for this Customer is not found in '
            #           'juniper Code:%s, Name:%s' %
            #           (code, jcustomer['General']['Name']))
            return None
        # Busco si tengo clientes con la misma referencia de cuenta:
        customer = self.env['res.partner'].search([
            ('customer_account_ref', '=', jcustomer[
                'InvoicingDetails']['AccountRefNumber'])])
        # Busco si tengo proveedores con la misma referencia de cuenta
        if not customer:
            supplier = self.env['res.partner'].search([
                ('supplier_account_ref', '=', jcustomer[
                    'InvoicingDetails']['AccountRefNumber'])])
            if supplier:
                # Marco el proveedor encontrado como cliente y almaceno su
                # referencia de cuenta e id
                values = {
                    'customer':
                        True,
                    'customer_account_ref':
                        jcustomer['InvoicingDetails']['AccountRefNumber'],
                    'code_ids': [(0, 0, {
                        'ptype': 'customer',
                        'partner_id': supplier.id,
                        'webservice_id': webservice,
                        'res_id': jbooking['Customer']['@Id']})]}
                supplier.write(values)
                _log.info(
                    'Supplier mark as Supplier, Id:%s ' % supplier.id)
                return supplier.id
            else:
                # Se crea el cliente nuevo en el sistema
                values = {
                    'name': jcustomer['General']['Name'],
                    'customer': True,
                    'supplier': False,
                    'is_company': True,
                    'street': jcustomer['Contact']['Address'],
                    'email': jcustomer['Contact']['Email'],
                    'phone': jcustomer['Contact']['Phone1'],
                    'mobile': jcustomer['Contact']['Mobile'],
                    'property_account_position': fiscal_position_id.id,
                    'customer_account_ref':
                    jcustomer['InvoicingDetails']['AccountRefNumber'],
                    'code_ids': [(0, 0, {
                        'ptype': 'customer',
                        'webservice_id': webservice,
                        'res_id': jbooking['Customer']['@Id']})]}
                customer = self.env['res.partner'].create(values)
                _log.info('Customer create Id:%s' % customer.id)
        else:
            # Comprobar si el id de juniper lo tenemos registrado en el sistema
            juniper_id = code_obj.search([
                ('partner_id', '=', customer.id), ('ptype', '=', 'customer'),
                ('res_id', '=', jbooking['Customer']['@Id']),
                ('webservice_id', '=', webservice)])
            if not juniper_id:
                juniper_id = code_obj.create({
                    'ptype': 'customer', 'partner_id': customer.id,
                    'webservice_id': webservice,
                    'res_id': jbooking['Customer']['@Id']})
            _log.info('Customer found Id: %s' % customer.id)

        return customer.id

    @api.model
    def create_supplier(self, jline=None, code=None, webservice=None):
        """
        ----------------------------------------------------------------------
        Buscamos el proveedor en el sistema por su identificador y filtrando
        por tipo supplier. De no encontrarlo, buscamos los partners por el
        campo juniper AccountRefNumber. Si encontramos un partner con ese
        dato, lo marcamos como proveedor.
        ----------------------------------------------------------------------
        :param
            jline: Linea de la reserva
            code: codigo de la reserva
        :return: Id partner
        ----------------------------------------------------------------------
        """
        juniper = Juniper(
            url=self.url,
            user=self.username,
            password=self.password)
        fiscal_position_id = self.env['account.fiscal.position'].search([
            ('name', 'ilike', 'Exempt')])
        code_obj = self.env['booking.webservice.partner.ref']
        # Cargo el proveedor desde juniper para obtener la referencia de cuenta
        jsupplier = juniper.supplier(SupplierId=jline['Supplier']['@Id'])
        # Comprobar si la referencia de cuenta viene rellena de juniper si
        # no salo y error en log.
        if not jsupplier['AccountRefNumber']:
            _log.info('AccountRefNumber for this Supplier is not found in '
                      'juniper Code:%s, Name:%s' % (code, jsupplier['Name']))
            ref = code_obj.search([('res_id', '=', jsupplier['@Id'])])
            supplier = ref and ref[0].partner_id or None
        else:
            # Buscar proveedores con el misma referencia de cuenta
            supplier = self.env['res.partner'].search([
                ('supplier_account_ref', '=', jsupplier['AccountRefNumber'])])
            supplier = supplier and supplier[0] or None

        if not supplier:
            # Buscar si existen clientes con la misma referencia de cuenta
            customer = self.env['res.partner'].search([
                ('customer_account_ref', '=', jsupplier['AccountRefNumber'])])
            if jsupplier['AccountRefNumber'] and customer:
                # Marco el cliente como proveedor y almaceno sus ids
                values = {
                    'supplier': True,
                    'supplier_account_ref': jsupplier['AccountRefNumber'],
                    'code_ids': [(0, 0, {
                        'ptype': 'supplier',
                        'partner_id': customer.id,
                        'webservice_id': webservice,
                        'res_id': jline['Supplier']['@Id']})]}
                customer.write(values)
                _log.info(
                    'Customer make as Supplier, id:%s' % customer.id)
                return customer.id
            else:
                # Se crea el proveedor nuevo en el sistema
                values = {
                    'name': jsupplier['Name'],
                    'supplier': True,
                    'customer': False,
                    'is_company': True,
                    'street': jsupplier['Address'],
                    'email': jsupplier['Email'],
                    'phone': jsupplier['Phone1'],
                    'property_account_position': fiscal_position_id.id,
                    'supplier_account_ref': jsupplier['AccountRefNumber'],
                    'code_ids': [(0, 0, {
                        'ptype': 'supplier',
                        'webservice_id': webservice,
                        'res_id': jline['Supplier']['@Id']})]}
                supplier = self.env['res.partner'].create(values)
                _log.info(
                    'Supplier create id:%s' % supplier.id)
        else:
            # Tengo el proveedor cargado en el sistema
            juniper_id = code_obj.search([
                ('partner_id', '=', supplier.id), ('ptype', '=', 'supplier'),
                ('res_id', '=', jline['Supplier']['@Id']),
                ('webservice_id', '=', webservice)])
            if not juniper_id:
                juniper_id = code_obj.create({
                    'ptype': 'supplier', 'partner_id': supplier.id,
                    'webservice_id': webservice,
                    'res_id': jline['Supplier']['@Id']})
            _log.info(
                'Supplier found Id:%s' % supplier.id)
        return supplier.id

    @api.model
    def create_zone(self, jline=None, code=None):
        """
        ----------------------------------------------------------------------
        Creacion de zona si no existe. A veces las reservas desde juniper
        vienen sin zona de venta
        ----------------------------------------------------------------------
        :param
            jline: Linea de reserva
            code: codigo de la reserva
        :return: id Zona
        ----------------------------------------------------------------------
        """
        zone = self.env['booking.zone'].search([
            ('juniper_id', '=', jline['Zone']['@Id'])])
        if not zone:
            if jline['Zone']['@Id'] and jline['Zone']['description']:
                values = {
                    'name': jline['Zone']['description'],
                    'province': (
                        jline['Zone'] and jline['Zone']['state'] or False),
                    'country': jline['Zone']['country'],
                    'juniper_id': jline['Zone']['@Id']}
                zone = self.env['booking.zone'].create(values)
                return zone.id
            else:
                return None
        return zone.id
