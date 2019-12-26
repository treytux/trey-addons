# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from .methabook import Methabook
from openerp import models, tools, fields, api, exceptions, _
import datetime
import json
import os
import requests
import logging
_log = logging.getLogger(__name__)


class BookingWebservice(models.Model):
    _inherit = 'booking.webservice'

    type = fields.Selection(
        string="Type",
        selection=[('juniper', 'Juniper'), ('methabook', 'Iboosy')],
        required=True)
    api_key = fields.Char(string='API Key')

    @api.multi
    def mt_check_conection(self, res):
        if res.status_code != requests.codes.ok:
            if res.status_code == 401:
                msg = _('ApiKey not valid.')
            else:
                msg = '%s, %s' % (res.status_code, res.reason)
            self.mt_webservice_log(_('Cannot conect to webservice.'), msg)
            return False
        return True

    @api.multi
    def mt_get_request_body(self, res):
        return json.loads(res.text, 'utf-8')['Export']

    @api.multi
    def mt_get_connection_credentials(self, test):
        if not test:
            bw_methabook_booking = self.env.ref(
                'booking_webservice_methabook.bw_methabook_booking')
            if not bw_methabook_booking:
                self.mt_webservice_log(_('None export URL'),
                                       'None Webservice Methabook Export URL.')
                return
        else:
            bw_methabook_booking = self.env.ref(
                'booking_webservice_methabook.bw_methabook_booking_test')
        return bw_methabook_booking

    @api.multi
    def mt_update_bookings_methabook(self, test=False):
        bw_methabook_booking = self.mt_get_connection_credentials(test)
        methabook = Methabook(bw_methabook_booking.url,
                              bw_methabook_booking.api_key)
        response = methabook.open_url(bw_methabook_booking.url)
        connection_ok = self.mt_check_conection(response)
        if not connection_ok:
            _log.info('X' * 80)
            _log.info(('Error connecting to booking platform.'))
            _log.info('X' * 80)
            raise exceptions.Warning(('Error connecting to booking platform.'))
        json_data = self.mt_get_request_body(response)
        msg = 'Start Updating Bookins Methabook.'
        _log.info('X' * 80)
        _log.info((msg))
        _log.info('X' * 80)
        self.mt_webservice_log(json_data, msg, 'info')
        json_processed, customers_list, suppliers_list, bookings_obj_list = (
            self.mt_booking_methabook(json_data))
        for type_element in ['booking', 'customer', 'supplier']:
            self.env['booking.webservice.job'].create({
                'date': fields.Datetime.now(),
                'amount_element': len(json_processed[type_element + 's']),
                'webservice_id': bw_methabook_booking.id,
                'object_model': type_element,
                'note': json_processed})
        msg = 'End Updating Bookins Methabook.'
        _log.info('X' * 80)
        _log.info((msg))
        _log.info('X' * 80)
        self.mt_webservice_log(json_processed, msg, 'info')
        json_processed['ExportId'] = json_data['ExportId']
        json_processed['ExportedAt'] = json_data['ExportedAt']
        json_obj_processed = json.dumps(json_processed)
        send_processed_bookings = {
            'json_obj_processed': json_obj_processed,
            'customers_list': customers_list,
            'suppliers_list': suppliers_list,
            'bookings_list': bookings_obj_list,
            'test': test}
        _log.info('X' * 80)
        _log.info(('Send processed bookings'))
        _log.info('X' * 80)
        self.mt_send_processed_bookings(send_processed_bookings)
        return True

    @api.multi
    def mt_booking_methabook(self, json_data):
        bookings_locator_list = []
        customers_list = []
        _log.info('X' * 80)
        _log.info(('time', fields.Datetime.now()))
        _log.info('X' * 80)
        customer_processed_list, customers_list = (
            self.mt_process_customers(json_data))
        self.env.cr.commit()
        _log.info('X' * 80)
        _log.info(('time post customer', fields.Datetime.now()))
        _log.info('X' * 80)
        supplier_processed_list, suppliers_list = (
            self.mt_process_suppliers(json_data))
        self.env.cr.commit()
        _log.info('X' * 80)
        _log.info(('time post suppliers', fields.Datetime.now()))
        _log.info('X' * 80)
        self.mt_process_zones(json_data)
        self.env.cr.commit()
        _log.info(('time post zones', fields.Datetime.now()))
        bookings_locator_list, bookings_obj_list = self.mt_process_bookings(
            json_data)
        self.env.cr.commit()
        _log.info(('time post Bookings proccess', fields.Datetime.now()))
        res = {'exportId': json_data['ExportId'],
               'exportedAt': json_data['ExportedAt'],
               'customers': customer_processed_list,
               'suppliers': supplier_processed_list,
               'bookings': bookings_locator_list}
        return res, customers_list, suppliers_list, bookings_obj_list

    @api.multi
    def mt_booking_log(self, booking_list, msg, type_log='error'):
        self.env['methabook.log'].add_log(
            'booking', None, 'booking', booking_list, _(msg), type_log)

    @api.multi
    def mt_webservice_log(self, objects, msg, type_log='error'):
        self.env['methabook.log'].add_log(
            'booking.webservice', None, 'booking', objects, _(msg), type_log)

    @api.multi
    def mt_process_bookings(self, json_data):
        booking_locator_list = []
        bookings_obj_list = []
        _log.info('Booking to process: %s' % len(
            json_data.get('Bookings', [])))
        total = len(json_data.get('Bookings'))
        for booking in json_data.get('Bookings', []):
            my_booking = self.mt_find_or_create_booking(booking)
            if not my_booking:
                continue
            booking_locator_list = (
                booking_locator_list + [{'locator': my_booking.name}])
            bookings_obj_list = bookings_obj_list + [my_booking]
            total -= 1
            _log.info('Remaining: %s' % total)
        self.mt_booking_log(
            json_data['Bookings'], booking_locator_list, 'bookings')
        return booking_locator_list, bookings_obj_list

    @api.multi
    def mt_process_customers(self, json_data):
        customers_account_list = []
        customers_list = []
        if json_data['Customers'] == []:
            self.env['methabook.log'].add_log(
                'res.partner', None, 'customer', customers_account_list,
                _('No customers processed'), 'info')
            return customers_account_list, customers_list
        for customer in json_data['Customers']:
            if not (customer['Account']).isdigit():
                self.env['methabook.log'].add_log(
                    'res.partner', None, 'customer',
                    customer, _('Customer Account is not digit'))
                continue
            my_customer = self.mt_find_or_create_partner('customer', customer)
            if not my_customer:
                self.env['methabook.log'].add_log(
                    'res.partner', None, 'customer',
                    customer, _('Customer Account is not digit'))
                continue
            customers_account_list = (
                customers_account_list + [{'account': customer['Account']}])
            customers_list.append(my_customer)
        self.env['methabook.log'].add_log(
            'res.partner', None, 'customer', customers_account_list,
            _('%s / %s customers processed') % (len(customers_account_list),
                                                len(json_data['Customers'])),
            'info')
        return customers_account_list, customers_list

    @api.multi
    def mt_process_suppliers(self, json_data):
        supplier_account_list = []
        suppliers_list = []
        if json_data['Suppliers'] == []:
            self.env['methabook.log'].add_log(
                'res.partner', None, 'supplier', supplier_account_list,
                _('No suppliers processed'), 'info')
            return supplier_account_list, suppliers_list
        for supplier in json_data['Suppliers']:
            if not (supplier['Account']).isdigit():
                self.env['methabook.log'].add_log(
                    'res.partner', None, 'supplier',
                    supplier, _('Supplier Account is not digit'))
                continue
            my_supplier = self.mt_find_or_create_partner('supplier', supplier)
            if not my_supplier:
                self.env['methabook.log'].add_log(
                    'res.partner', None, 'supplier',
                    supplier, _('Supplier Account is not digit'))
                continue
            supplier_account_list = (
                supplier_account_list + [{'account': supplier['Account']}])
            suppliers_list.append(my_supplier)
        self.env['methabook.log'].add_log(
            'res.partner', None, 'supplier', supplier_account_list,
            _('%s / %s suppliers processed') % (len(supplier_account_list),
                                                len(json_data['Suppliers'])),
            'info')
        return supplier_account_list, suppliers_list

    @api.multi
    def mt_process_zones(self, json_data):
        created_zones = []
        if not json_data['Zones']:
            return
        for zone in json_data['Zones']:
            zone_id = self.mt_update_or_create_zone(zone)
            created_zones.append(zone_id)
        self.env['methabook.log'].add_log(
            'booking.zone', None, 'zone', created_zones,
            _('%s / %s zones processed') % (len(created_zones),
                                            len(json_data['Zones'])),
            'info')
        return created_zones

    @api.multi
    def mt_check_booking_state(self, booking, states_dic):
        if booking['Status'] not in states_dic:
            msg = _('Booking %s with state %s not found' % (booking['Locator'],
                                                            booking['Status']))
            self.mt_booking_log(booking, msg)
            return False
        return True

    @api.multi
    def mt_get_currency(self, code):
        currency = self.env['res.currency'].search([('name', '=', code)])
        return currency and currency.id or False

    @api.multi
    def mt_time_format(self, date_string_raw, only_day=None):
        cleanDatetime = date_string_raw.replace('T', ' ').strip('Z').split('.')
        date_format = '%Y-%m-%d'
        time_format = '%Y-%m-%d %H:%M:%S'
        if only_day:
            return datetime.datetime.strptime(
                cleanDatetime[0], date_format).strftime(date_format)
        src_tstamp_str = datetime.datetime.strptime(
            cleanDatetime[0], time_format).strftime(time_format)
        difference_time = int(tools.misc.server_to_local_timestamp(
            src_tstamp_str, time_format, '%H', self.env.user.tz))
        booking_time_format = int(
            cleanDatetime[0].split(' ')[1].rsplit(':')[0])
        # Restamos las horas que nos añadira el servidor tras guardar el campo
        normal = datetime.datetime.strptime(cleanDatetime[0], time_format)
        time_diff = booking_time_format - difference_time
        final_date = normal + datetime.timedelta(hours=time_diff)
        diff_date = (
            normal.strftime(date_format) != final_date.strftime(date_format))
        if diff_date:
            adjust_date = normal - datetime.timedelta(hours=difference_time)
            adjust_hour = adjust_date.replace(
                hour=int(final_date.strftime('%H')))
            return adjust_hour
        return final_date

    @api.multi
    def mt_get_booking_dict(self, booking, customer, holder, states_dic):
        webservice_id = self.env.ref(
            'booking_webservice_methabook.bw_methabook_booking')
        # Fechas con horas y minutos
        # 'date': self.time_format(booking['CreationDate']),
        # 'date_modify': self.time_format(booking['ModificationDate']),
        data = {
            'name': booking['Locator'],
            'api_info': booking,
            'date': self.mt_time_format(booking['CreationDate']),
            'date_modify': self.mt_time_format(booking['ModificationDate']),
            'date_limit': self.mt_time_format(
                booking['ExpirationDate'], 'only_day'),
            # primero añado date_end para no que no este vacio.
            # Luego asigno la fecha del checkOut al recorrer el booking.line
            'date_end': self.mt_time_format(
                booking['ExpirationDate'], 'only_day'),
            'agency_id': customer and customer.id,
            'holder_id': holder.id,
            'methabook_id': webservice_id and webservice_id.id or None,
            'state': states_dic[booking['Status']],
            'is_pay_tpv': booking['PaidByTPV'] or False,
            'date_tpv': fields.Date.today() if booking['PaidByTPV'] else None}
        return data

    @api.multi
    def mt_get_booking_line_dict(
            self, service_line, my_booking, supplier, zone_raw):
        webservice_id = self.env.ref(
            'booking_webservice_methabook.bw_methabook_booking')
        zone = zone_raw.get('zone_id', None)
        if 'CountryISOCode' in service_line:
            service_country_id = self.mt_get_service_country(
                code=service_line['CountryISOCode'])
        else:
            service_country_id = None
        return {
            'name': service_line['Description'],
            'booking_id': my_booking.id,
            'methabook_id': webservice_id and webservice_id.id or None,
            'supplier_id': supplier and supplier.id or None,
            'ex_reference': service_line['ExternalLocator'],
            'selling_price': service_line['Price']['Sale']['Gross'],
            'commission': service_line['Price']['Sale']['Commission'],
            'cost_net': service_line['Price']['Purchase']['Net'],
            'cost_gross': service_line['Price']['Purchase']['Gross'],
            'pricecommission': service_line['Price']['Purchase']['Commission'],
            'amount_untaxed': service_line['Price']['Sale']['Gross'],
            'amount': service_line['Price']['Sale']['Gross'],
            'cost_currency_id': self.mt_get_currency(
                service_line['Price']['Purchase']['CurrencyCode']),
            'sell_currency_id': self.mt_get_currency(
                service_line['Price']['Sale']['CurrencyCode']),
            'date_init': self.mt_time_format(
                service_line['CheckInDate'], 'only_day'),
            'date_end': self.mt_time_format(
                service_line['CheckOutDate'], 'only_day'),
            'date': my_booking.date,
            'zone_id': zone and zone.id or None,
            'zone_province': zone_raw.get('zone_province', ''),
            'zone_country': zone_raw.get('zone_country', ''),
            'service_country_id': service_country_id}

    @api.multi
    def mt_get_customer(self, booking):
        if not booking['Customer'].get('Account', False):
            self.env['methabook.log'].add_log(
                'res.partner', None, 'booking', booking,
                _('Json without customer account'))
        else:
            customers = self.mt_get_partner(booking['Customer'], 'customer')
            customers = customers.get('partner')
            if not customers:
                self.env['methabook.log'].add_log(
                    'res.partner', booking['Customer']['Account'], 'booking',
                    booking, _('Customer with account %s not found') %
                    booking['Customer']['Account'])
                return False
            return customers and customers[0] or None
        return None

    @api.multi
    def mt_get_supplier(self, service_line, booking):
        if not service_line['Supplier'].get('Account', False):
            self.env['methabook.log'].add_log(
                'res.partner', None, 'booking', booking,
                _('Json without Supplier account'))
        else:
            supplier_account = service_line['Supplier']
            suppliers = self.mt_get_partner(supplier_account, 'supplier')
            suppliers = suppliers.get('partner')
            if not suppliers:
                self.env['methabook.log'].add_log(
                    'res.partner', supplier_account['Account'], 'booking',
                    booking, _('Supplier with account %s not found') %
                    supplier_account['Account'])
            return suppliers and suppliers[0] or None
        return None

    @api.multi
    def mt_get_zone(self, service_line, booking):
        if not service_line.get('Zone', False):
            return {'zone_id': None,
                    'zone_province': None,
                    'zone_country': None}
        zone_raw = (service_line['Zone']['Name']).split(',')
        zones = None
        zone_province = None
        zone_country = None
        if len(zone_raw) == 2:
            zone_country = zone_raw[1]
        if len(zone_raw) == 3:
            zone_province = zone_raw[1]
            zone_country = zone_raw[2]
        if 'Code' in service_line['Zone']:
            zone_code = service_line['Zone']['Code']
            zones = self.env['booking.zone'].search([
                ('methabook_id', '=', zone_code)])
            if not zones:
                msg = _('Zone with code %s not found') % zone_code
                self.env['methabook.log'].add_log('booking.zone', zone_code,
                                                  'booking', booking, msg)
        return {'zone_id': zones and zones[0] or None,
                'zone_province': zone_province,
                'zone_country': zone_country}

    @api.multi
    def mt_get_service_country(self, code=None):
        return self.env['res.country'].search([('code', '=', code)]).id

    @api.multi
    def mt_find_or_create_booking(self, booking, _cache=None):
        if _cache is None:
            _cache = {}
        states_dic = {'Confirmed': 'confirmed',
                      'OnRequest': 'draft',
                      'Paid': 'paid',
                      'CancelledBySystemOrAdmin': 'canceled',
                      'CancelledByCustomer': 'cancelcus',
                      'Error': 'canceled'}

        if not self.mt_check_booking_state(booking, states_dic):
            return None
        _log.info('Search or Create booking:%s' % booking['Locator'])
        my_booking = self.env['booking'].search(
            [('name', '=', booking['Locator'])])
        if not my_booking:
            my_booking = self.mt_bookings_lines_processor(booking, states_dic)
        else:
            if booking['PaidByTPV'] and not my_booking.is_pay_tpv:
                my_booking.write({
                    'is_pay_tpv': True,
                    'date_tpv': fields.Date.today()})
            if my_booking.state in ('paid', 'done'):
                my_booking_has_invoices = [
                    True for i in my_booking.invoices if i.state != 'draft']
                if True in my_booking_has_invoices:
                    my_booking.update_after_invoiced = True
                    self.env['methabook.log'].add_log(
                        'booking', None, 'booking', booking,
                        _('Invoiced booking %s no updated.') % my_booking.name,
                        'error')
            my_booking = self.mt_bookings_lines_processor(
                booking, states_dic, my_booking)
        return my_booking and my_booking or False

    @api.multi
    def mt_bookings_lines_processor(
            self, booking, states_dic, my_booking=None):
        try:
            booking_lines = self.env['booking.line']
            update_mode = False
            total_amount_selling = 0
            total_amount_cost_gross = 0
            total_amount_cost_net = 0
            total_amount_commission = 0
            holder = self.mt_get_booking_holder(booking['Holder'])
            customer = self.mt_get_customer(booking)
            if not customer:
                return False
            if not holder:
                return False
            data = self.mt_get_booking_dict(
                booking, customer, holder, states_dic)
            supplier = self.mt_get_supplier(
                booking['Services'][0]['Accommodation'], booking)
            if not supplier:
                return False
            if not my_booking:
                my_booking = self.env['booking'].create(data)
            else:
                my_booking.write(data)
                update_mode = True
            self.env.cr.commit()
            new_ex_reference_list = []
            for service in booking['Services']:
                is_new_line = False
                service_line = service['Accommodation']
                if update_mode:
                    ex_reference = service_line['ExternalLocator']
                    new_ex_reference_list = \
                        new_ex_reference_list + [ex_reference]
                    my_booking_lines = booking_lines.search([
                        ('booking_id', '=', my_booking.id),
                        ('ex_reference', '=', ex_reference)])
                zone_raw = self.mt_get_zone(service_line, booking)
                line_vals = self.mt_get_booking_line_dict(
                    service_line, my_booking, supplier, zone_raw)
                date_end = (
                    self.mt_time_format(
                        service_line['CheckOutDate'], 'only_day'))
                date_init = (
                    self.mt_time_format(
                        service_line['CheckInDate'], 'only_day'))
                total_amount_selling += service_line['Price']['Sale']['Gross']
                total_amount_commission += (
                    service_line['Price']['Sale']['Commission'])
                total_amount_cost_gross += \
                    service_line['Price']['Purchase']['Gross']
                total_amount_cost_net += \
                    service_line['Price']['Purchase']['Net']
                if update_mode:
                    if not my_booking_lines:
                        new_line = booking_lines.create(line_vals)
                        is_new_line = True
                    else:
                        my_booking_lines[0].write(line_vals)
                        if my_booking_lines[0].invoiced:
                            my_booking_lines[0].update_after_invoiced = True
                    if my_booking.invoices and is_new_line:
                        for invoice in my_booking.invoices:
                            for line in invoice.invoice_line:
                                line.booking_line_id = new_line.id
                                self.env.cr.commit()
                    old_ex_reference_list = []
                    for line in my_booking.booking_line:
                        old_ex_reference_list = (
                            old_ex_reference_list + [line.ex_reference])
                    lines_to_delete = list(set(old_ex_reference_list) - set(
                        new_ex_reference_list))
                    b_lines_delete = booking_lines.search(
                        [('ex_reference', 'in', lines_to_delete)])
                    if b_lines_delete:
                        # for b_line_delete in b_lines_delete:
                        #     invoice_line_delete = self.env[
                        #         'account.invoice.line'].search(
                        #         [('booking_line_id', '=', b_line_delete.id)])
                        #     if invoice_line_delete:
                        #         invoice_line_delete.booking_line_id = None
                        b_lines_delete.unlink()
                        self.env.cr.commit()
                        msg = _('Lines deleted after booking update.')
                        self.mt_booking_log(lines_to_delete, msg, 'info')
                else:
                    booking_lines.create(line_vals)
            my_booking.write({
                'date_end': date_end,
                'date_init': date_init,
                'amount_selling': total_amount_selling,
                'amount_commission':  total_amount_commission,
                'amount_cost_gross': total_amount_cost_gross,
                'amount_cost_net': total_amount_cost_net})
            return my_booking
        except Exception as e:
            _log.warning(
                'Error create booking line: %s description: %s' %
                my_booking and my_booking.name or '', e)
            self.env.cr.commit()
            return False

    @api.multi
    def mt_update_or_create_zone(self, zone):
        def _get_zone_info(zone):
            province = None
            country = None
            if zone.get('ParentZone'):
                parent_zone = self.env['booking.zone'].search(
                    [('methabook_id', '=', zone['ParentZone'])])
                if parent_zone and not parent_zone.parent_zone_id:
                    country = parent_zone.name
                else:
                    province = parent_zone.name
                    parent_country = self.env['booking.zone'].search(
                        [('methabook_id', '=', parent_zone.parent_zone_id)])
                    country = parent_country and parent_country.name or None
            values = {'name': zone['Name'],
                      'province': province,
                      'country': country,
                      'methabook_id': zone['Code']}
            if 'parent_zone_id' in zone:
                values.update({'parent_zone_id': zone['ParentZone']})
            return values

    def mt_get_booking_holder(self, booking_holder, _cache=None):
        holder = self.mt_update_or_create_holder(booking_holder)
        return holder

    def mt_update_or_create_holder(self, booking_holder):
        holders = self.env['booking.holder']
        domain = [('name', '=', ' '.join([booking_holder.get('Name', ''),
                                          booking_holder.get('Surname', '')]))]
        my_holders = holders.search(domain)
        if not my_holders:
            data = {'name': ' '.join([booking_holder.get('Name', ''),
                                      booking_holder.get('Surname', ''), ' '])}
            my_holder = holders.create(data)
            return my_holder
        return my_holders[0]

    def mt_valid_partner_account(self, partner):
        case1 = not partner['Account'] or (
            type(partner['Account']) == 'str' and not
            partner['Account'].isdigit())
        case2 = (
            type(partner['Account']) == 'dict' and not
            partner['Account'].isdigit())
        case3 = not partner['Account'].isdigit()
        if case1 or case2 or case3:
            return False
        return True

    def mt_get_partner(self, partner, ttype):

        def _get_customer(partner_account):
            my_partners = self.env['res.partner'].search([
                ('customer_account_ref_methabook', '=', partner_account)])
            if not my_partners:
                my_partners = self.env['res.partner'].search([
                    ('customer_account_ref', '=', partner_account)])
                if my_partners and my_partners[0]:
                    my_partners[0].customer_account_ref_methabook = (
                        partner_account)
            return my_partners

        def _get_supplier(partner_account):
            my_partners = self.env['res.partner'].search([
                ('supplier_account_ref_methabook', '=', partner_account)])
            if not my_partners:
                my_partners = self.env['res.partner'].search([
                    ('supplier_account_ref', '=', partner_account)])
                if my_partners and my_partners[0]:
                    my_partners[0].supplier_account_ref_methabook = (
                        partner_account)
            return my_partners

        if not self.mt_valid_partner_account(partner):
            return {}
        partner_account = int(partner['Account'])
        if ttype == 'customer':
            customer = True
            supplier = False
            my_partners = _get_customer(partner_account)
            if not my_partners:
                my_partners = _get_supplier(partner_account)
                if my_partners and my_partners[0]:
                    my_partners[0].write({
                        'customer_account_ref_methabook': partner_account,
                        'customer': True})
                self.env.cr.commit()
        else:
            customer = False
            supplier = True
            my_partners = _get_supplier(partner_account)
            if not my_partners:
                my_partners = _get_customer(partner_account)
                if my_partners and my_partners[0]:
                    my_partners[0].write({
                        'supplier_account_ref_methabook': partner_account,
                        'supplier': True})
                self.env.cr.commit()
        return {'partner': my_partners and my_partners[0] or None,
                'customer': customer,
                'supplier': supplier}

    def mt_get_partner_data_dict(
            self, partner, ttype, customer, supplier, country,
            fiscal_positions):
        partner_data = {
            'is_company': True,
            'street': partner['Location']['Address'],
            'city': partner['Location']['City'],
            'zip': partner['Location']['PostalCode'],
            'country_id': country and country.id or None,
            'email': partner['Email'],
            'phone': partner['Phone'],
            'property_account_position':
                fiscal_positions and
                fiscal_positions[0].id or None}
        if ttype == 'customer':
            partner_data['name'] = partner['LegalName']
            partner_data['customer'] = True
            partner_data['supplier'] = supplier
            partner_data['customer_account_ref_methabook'] = partner['Account']
        if ttype == 'supplier':
            partner_data['name'] = partner['FiscalName']
            partner_data['customer'] = customer
            partner_data['supplier'] = True
            partner_data['supplier_account_ref_methabook'] = partner['Account']
        return partner_data

    def mt_find_or_create_booking_webservice_partner_ref(
            self, ptype, partner, my_partner):
        webservice = self.env['booking.webservice'].search(
            [('type', '=', 'methabook')])[0]
        b_w_partner_refs = self.env['booking.webservice.partner.ref']
        methabook_id = b_w_partner_refs.search([
            ('ptype', '=', ptype),
            ('partner_id', '=', my_partner.id),
            ('webservice_id', '=', webservice.id),
            ('res_id', '=', partner['Account'])])
        if not methabook_id:
            methabook_id = b_w_partner_refs.create({
                'ptype': ptype,
                'partner_id': my_partner.id,
                'webservice_id': webservice.id,
                'res_id': partner['Account']})
        return methabook_id

    def mt_find_or_create_partner(self, ptype, partner):
        def _partner_log(partner, ptype, msg):
            self.env['methabook.log'].add_log(
                'res.partner', partner['Account'], ptype, partner, msg)

        if not self.mt_valid_partner_account(partner):
            return None
        partner_dict = self.mt_get_partner(partner, ptype)
        my_partner = partner_dict.get('partner')
        is_supplier = partner_dict.get('supplier')
        is_customer = partner_dict.get('customer')
        fiscal_positions = self.env['account.fiscal.position'].search(
            [('name', 'ilike', 'Exempt')])
        country = self.env['res.country'].search(
            [('code', '=', partner['Location']['Country'])])
        if not country:
            msg = _('Country with name %s not found'
                    ) % partner['Location']['Country']
            _partner_log(partner, ptype, msg)
        partner_data = self.mt_get_partner_data_dict(
            partner, ptype, is_customer, is_supplier, country,
            fiscal_positions)
        if not my_partner:
            try:
                my_partner = self.env['res.partner'].create(partner_data)
                my_partner.write({'vat': ''.join(
                    [partner['Location']['Country'], partner['Vat']])})
            except exceptions.ValidationError as e:
                _partner_log(partner, ptype, e)
                my_partner.write({'vat': None})
        else:
            try:
                partner_data['vat'] = ''.join([partner['Location']['Country'],
                                              partner['Vat']])
                my_partner.write(partner_data)
            except exceptions.ValidationError as e:
                _partner_log(partner, ptype, e)
                partner_data['vat'] = None
                my_partner.write(partner_data)
        self.mt_find_or_create_booking_webservice_partner_ref(
            ptype, partner, my_partner)
        return my_partner

    @api.multi
    def mt_send_processed_bookings(self, data_dict):
        if data_dict['test']:
            return True
        bw_methabook_confirm = self.env.ref(
            'booking_webservice_methabook.bw_methabook_confirm')
        headers = {'Content-Type': 'application/json; charset=utf-8',
                   'Api-Key': bw_methabook_confirm.api_key}
        methabook = Methabook(bw_methabook_confirm.url,
                              bw_methabook_confirm.api_key)
        res = requests.put(methabook.url, headers=headers,
                           data=data_dict['json_obj_processed'])
        connection_ok = self.mt_check_conection(res)
        if not connection_ok:
            msg = 'Error marking bookings as processed'
            self.mt_webservice_log(res.text, msg)
            raise exceptions.Warning(
                _('Error connecting to booking platform to confirm bookings'))
        else:
            for customer in data_dict['customers_list']:
                customer.processed_ok = True
            for supplier in data_dict['suppliers_list']:
                supplier.processed_ok = True
            for booking in data_dict['bookings_list']:
                booking.processed_ok = True
            webservice_job = self.env['booking.webservice.job']
            webservice_job.create({
                'date': fields.Datetime.now(),
                'webservice_id': bw_methabook_confirm.id,
                'amount_element': len(data_dict['bookings_list']),
                'object_model': 'booking',
                'note': data_dict['bookings_list']})
            webservice_job.create({
                'date': fields.Datetime.now(),
                'webservice_id': bw_methabook_confirm.id,
                'amount_element': len(data_dict['customers_list']),
                'object_model': 'customer',
                'note': data_dict['customers_list']})
            webservice_job.create({
                'date': fields.Datetime.now(),
                'webservice_id': bw_methabook_confirm.id,
                'amount_element': len(data_dict['suppliers_list']),
                'object_model': 'supplier',
                'note': data_dict['suppliers_list']})
        return True

    @api.multi
    def mt_send_booking_as_paid(self, booking):
        bw_methabook_paid = self.env.ref(
            'booking_webservice_methabook.bw_methabook_paid')
        data = {'bookings': [{'locator': booking.name}]}
        data_json = json.dumps(data)
        headers = {'Content-Type': 'application/json; charset=utf-8',
                   'Api-Key': bw_methabook_paid.api_key}
        methabook = Methabook(bw_methabook_paid.url, bw_methabook_paid.api_key)
        response = requests.put(methabook.url, headers=headers, data=data_json)
        connection_ok = self.mt_check_conection(response)
        if not connection_ok:
            raise exceptions.Warning(
                _('Error connecting to booking platform to set this invoice '
                  'as paid. Try again later or contact with an admin.'))
        msg = 'Booking marked as paid: %s' % booking.name
        self.mt_webservice_log(booking.name, msg, 'info')
        self.env['booking.webservice.job'].create({
            'date': fields.Datetime.now(),
            'amount_element': len(booking),
            'webservice_id': bw_methabook_paid.id,
            'object_model': 'booking',
            'note': booking})
        return True

    @api.multi
    def mt_check_customer_credit_limit(
            self, customer, days_to_notify_customer):
        def is_time_to_notify(customer, days_to_notify_customer):
            credit_date = datetime.datetime.strptime(
                customer.credit_limit_reached_date, '%Y-%m-%d').date()
            time_to_notify = (datetime.date.today() - credit_date)
            created_today = datetime.date.today() == credit_date
            in_period = int(time_to_notify.days) >= days_to_notify_customer
            return (created_today or in_period) and True or False

        if abs(int(customer.credit)) > int(customer.credit_limit):
            if customer.credit_limit_reached:
                time_to_notify = is_time_to_notify(
                    customer, days_to_notify_customer)
                if time_to_notify:
                    # no tiene saldo y han pasado X dias, no se hace put
                    self.mt_send_customer_credit_email(customer, 'subscribe')
            else:
                # no tiene saldo y no esta avisado
                customer.write({
                    'credit_limit_reached': True,
                    'credit_limit_reached_date': datetime.date.today()
                })
                self.mt_put_customer_credit_info(customer, False)
                self.mt_send_customer_credit_email(customer, 'subscribe')
        else:
            if customer.credit_limit_reached:
                _log.info(('%s vuelve a tener saldo' % customer.name))
                customer.credit_limit_reached = False
                self.mt_put_customer_credit_info(customer, True)
                self.mt_send_customer_credit_email(customer, 'unsubscribe')
            # SIQUIENTE MEJORA EN DESVIOS
            # else:
                # Tiene saldo, limited_research=False (situacion normal)
                # - alcanza un 80%  de credito concedido??
                # if customer.credit_limit*100/customer.credit >= 0.8:
                # -notificariamos "queda un 80%"
                # send_customer_credit_email()
        return True

    @api.multi
    def mt_send_customer_credit_email(self, customer, status):
        mail_servers = self.env['ir.mail_server'].search([])
        if not mail_servers:
            self.env['methabook.log'].add_log(
                'customer', None, 'customer', customer,
                _('Can not send credit email: no mail server defined.'),
                'error')
            return False
        if status == 'subscribe':
            template = self.env.ref(
                'booking_webservice_methabook.email_credit_limit_subscribe')
        if status == 'unsubscribe':
            template = self.env.ref(
                'booking_webservice_methabook.email_credit_limit_unsubscribe')
        template.write({
            'template.email_from': customer.company_id.email,
            'template.reply_to': customer.company_id.email,
            'template.email_to': customer.email,
            'template.email_cc': customer.company_id.email,
        })
        template.send_mail(customer.company_id.id, force_send=True)
        return True

    @api.multi
    def mt_put_customer_credit_info(self, customer, credit_ok):
        bw_methabook_change_credit = self.env.ref(
            'booking_webservice_methabook.bw_methabook_change_credit')
        headers = {'Content-Type': 'application/json; charset=utf-8',
                   'Api-Key': bw_methabook_change_credit.api_key}
        data_json = json.dumps({
            'Account': customer.customer_account_ref_methabook,
            'WithCredit': credit_ok})
        response = requests.put(bw_methabook_change_credit.url,
                                headers=headers, data=data_json)
        connection_ok = self.mt_check_conection(response)
        if not connection_ok:
            self.env['methabook.log'].add_log(
                'res.partner',
                customer.customer_account_ref_methabook, 'customer',
                _('Error conecting to platform to update customer '
                  'credit: %s') % credit_ok, customer.name)
            return False
        self.env['methabook.log'].add_log(
            'res.partner', None, 'customer',
            customer, _('Customer %s ,with ID: %s credit update to: %s') % (
                customer.name, customer.id, credit_ok))
        self.env['booking.webservice.job'].create({
            'date': fields.Datetime.now(),
            'amount_element': len(customer),
            'webservice_id': bw_methabook_change_credit.id,
            'object_model': 'booking',
            'note': customer})

    @api.multi
    def mt_update_customer_credit_methabook(self):
        customers = self.env['res.partner'].search([
            ('customer', '=', True),
            ('customer_account_ref_methabook', '!=', False)])
        company = self.env['res.company'].search([])[0]
        for customer in customers:
            self.mt_check_customer_credit_limit(
                customer, int(company.days_to_notify_customer))
        return True

    @api.multi
    def mt_first_load_bookings_json(self, mode='file', booking_file=None):
        """
        Carga informacion de clientes, proveedores y reservas desde fichero
        :param mode: file-> manual load, booking-> query booking a generate
        file to load
        :param booking_file: booking file
        """
        def get_path(*relative_path):
            path = '../../tests/loads'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)
        _log.info('X' * 80)
        if mode == 'file':
            file_name = 'export_104880_500.json'
            path = get_path(file_name)
            text_data = open(path, 'r').read()
            json_data = json.loads(text_data)['Export']
            _log.info(('Utilizando JSON preload %s' % file_name))
            _log.info('X' * 80)
            msg = 'Start First Updating Bookins Methabook.'
        elif mode == 'booking':
            text_data = open(booking_file, 'r').read()
            json_data = json.loads(text_data)['Export']
            _log.info(('Utilizando JSON booking %s' % booking_file))
            _log.info('X' * 80)
            msg = 'Start from Query Wizard Updating Bookins Methabook.'
        self.mt_webservice_log(json_data, msg, 'info')
        json_processed, customers_list, suppliers_list, bookings_list = (
            self.mt_booking_methabook(json_data))
        webservice = self.env.ref(
            'booking_webservice_methabook.bw_methabook_booking')
        for type_element in ['booking', 'customer', 'supplier']:
            self.env['booking.webservice.job'].create({
                'date': fields.Datetime.now(),
                'amount_element': len(
                    json_processed[type_element + 's']),
                'webservice_id': webservice.id,
                'object_model': type_element,
                'note': json_processed})
        msg = 'End First Updating Bookins Methabook.'
        self.mt_webservice_log(json_processed, msg, 'info')

    @api.model
    def mt_create_booking_invoice_methabook(self):
        def create_invoice(journal, booking, change_factor):
            invoice_id = self.env['account.invoice'].create({
                'journal_id': journal.invoice_journal_id.id,
                'currency_id': booking.currency_id.id,
                'date_invoice': booking.date_end,
                'partner_id': booking.agency_id.id,
                'origin': booking.name,
                'name': booking.name,
                'type': 'out_invoice',
                'fiscal_position':
                    booking.agency_id.property_account_position.id,
                'booking_id': booking.id,
                'account_id': booking.agency_id.property_account_receivable.id,
                'currency_rate': change_factor})
            product_id = self.env.user.company_id.product_id
            self.env['account.invoice.line'].create({
                'account_id': product_id.property_account_income.id,
                'product_id': product_id.id,
                'quantity': 1,
                'uos_id': product_id.uom_id.id,
                'invoice_id': invoice_id.id,
                'name': booking.name,
                'price_unit': booking.amount_selling})
            _log.info(('invoiced', invoice_id.date_invoice))
            return invoice_id

        def mt_compute_change_factor(booking):
            company_currency_id = self.env.user.company_id.currency_id
            if booking.currency_id.id == company_currency_id.id:
                change_factor = 1
            else:
                context = self.env.context.copy()
                context['date'] = booking.date
                change_factor = booking.currency_id.with_context(
                    context)._get_conversion_rate(
                        to_currency=company_currency_id,
                        from_currency=booking.currency_id)
            return change_factor

        def mt_get_booking_journal(booking, invoice_obj, journal_obj):
            journal = self.env.user.company_id.journal_ids.filtered(
                lambda x: x.currency_id.id == booking.currency_id.id)
            if not journal:
                journal = self.env.user.company_id.journal_ids.filtered(
                    lambda x: x.default is True)
                if not journal:
                    journal_id = invoice_obj.default_get(
                        ['journal_id'])['journal_id']
                    journal = journal_obj.browse(journal_id)
            return journal

        bookings = self.env['booking'].search([
            ('methabook_id', '>', 0),
            ('state', 'not in', ('canceled', 'cancelcus')),
            ('invoiced', '=', False),
            ('date_end', '<', fields.Datetime.now())])
        self.env['methabook.log'].add_log(
            'invoice', None, 'booking', '',
            _('Starting creating booking customer invoices.'), 'info')
        bookings_invoiced = []
        invoice_ids = []
        invoice_obj = self.env['account.invoice']
        journal_obj = self.env['account.journal']
        log_obj = self.env['methabook.log']
        if not bookings:
            log_obj.add_log('invoice', None, 'booking', '',
                            _('No bookings to be invoiced.'), 'info')
            return True
        for booking in bookings:
            journal = mt_get_booking_journal(booking, invoice_obj, journal_obj)
            change_factor = mt_compute_change_factor(booking)
            invoice_id = create_invoice(journal, booking, change_factor)
            booking.invoiced = True
            invoice_id.button_compute()
            invoice_ids = invoice_ids + [invoice_id]
            bookings_invoiced = bookings_invoiced + [
                (booking.name).encode('utf-8')]
        log_obj.add_log('invoice', None, 'booking', ' '.join([
            'Bookigs:', str(bookings_invoiced),
            'Invoices:', str(invoice_ids)]),
            _('End Booking customer invoices creation.'), 'info')

    @api.multi
    def mt_preload_booking_zones(self):
        def get_path(*relative_path):
            path = '../../tests/json_test'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)

        def _create_zone(zone, zones, zone_obj):
            myzone = zone_obj.search([
                ('methabook_id', '=', zone['Code']),
                ('name', '=', zone['Name'])])
            if myzone:
                return
            has_parent = True if zone['ParentZone'] is not None else False
            if has_parent:
                parent_zone_in_odoo = zone_obj.search([
                    ('methabook_id', '=', zone['ParentZone'])])
                parent_zone_in_odoo = parent_zone_in_odoo if len(
                    parent_zone_in_odoo) == 1 else False
                if parent_zone_in_odoo:
                    new_zone = self.env['booking.zone'].create({
                        'name': zone['Name'],
                        'methabook_id': zone['Code'],
                        'parent_zone_id': parent_zone_in_odoo.methabook_id})
                    return new_zone
                in_my_zones_js = filter(
                    lambda x: x['Code'] == zone['ParentZone'],
                    data['Export']['Zones'])
                if in_my_zones_js:
                    _create_zone(in_my_zones_js[0], zones, zone_obj)
                return
            zone_without_parent = zone_obj.create({
                'name': zone['Name'],
                'methabook_id': zone['Code']})
            return zone_without_parent

        json_data = open(get_path('zones_test.json'))
        data = json.load(json_data)
        zones = data['Export']['Zones']
        zone_obj = self.env['booking.zone']
        for zone in zones:
            if zone['Code'] == zone['ParentZone']:
                _log.info(('ERROR ZONE CODE, la zona %s tiene como codigo %s y'
                           ' su zona padre es %s' % (zone['Name'],
                                                     zone['Code'],
                                                     zone['ParentZone'])))
                raise exceptions.Warning(
                    ('Zone and Parent Zone cant have the same code'))
            if not zone['Code'].isdigit():
                _log.info(('Booking zone con identificador no numerico'))
                raise exceptions.Warning(
                    ('Booking zone con identificador no numerico'))
            _create_zone(zone, zones, zone_obj)
        return True

    @api.multi
    def mt_button_manual_update_booking(self):
        # self._run_booking_methabook_update()
        self.mt_first_load_bookings_json()

    @api.multi
    def mt_button_preload_booking_zones(self):
        self.mt_preload_booking_zones()

    @api.model
    def _run_mt_booking_methabook_update(self):
        self.mt_update_bookings_methabook()

    @api.model
    def _run_mt_customer_credit_methabook_update(self):
        self.update_customer_credit_methabook()

    @api.model
    def _run_mt_customer_invoice_methabook_create(self):
        self.mt_create_booking_invoice_methabook()
