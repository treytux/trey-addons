# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain
from openerp.addons.l10n_es_payment_order.wizard.log import Log
import datetime


class PaymentKutxa(object):
    def __init__(self, env):
        self.env = env
        self.converter = PaymentConverterSpain()

    def create_file(self, order, lines):
        self.order = order
        self.num_records = 0
        self.number = 0
        if self.order.mode.type.code == 'payment_kutxa':
            txt_file = self._pop_header()
            for line in lines:
                txt_file += self._pop_beneficiary(line)
                txt_file += self._pop_detail(line)
                self.num_records += 1
            txt_file += self._pop_totals(line)
        return txt_file

    def _pop_header(self):
        all_text = ''
        for i in range(3):
            text = '510'
            text += str(i + 1)
            vat = self.order.mode.bank_id.partner_id.vat
            if not vat:
                raise Log(
                    ('Error: VAT of account not established \
                    for the account %s.\
                    ') % self.order.mode.bank_id.acc_number)
            vat = vat.replace("ES", "")
            if len(vat) < 10:
                    fill = 10 - len(vat)
                    vat = (fill * ' ') + vat
            elif len(vat) > 10:
                vat = vat[:10]
            text += vat
            if (i + 1) == 1:
                text += datetime.date.today().strftime('%d%m%y')
                ref = self.order.reference
                ref = ref.replace('/', '_')
                if len(ref) <= 8:
                        fill = 8 - len(ref)
                        ref += fill * ' '
                elif len(ref) > 8:
                    ref = ref[:8]
                text += ref
                payer = self.order.mode.bank_id.partner_id.name
                if len(payer) <= 40:
                    fill = 40 - len(payer)
                    payer += fill * ' '
                elif len(payer) > 40:
                    payer = payer[:40]
                text += payer
                account = self.order.mode.bank_id.acc_number
                account = account.replace(' ', '')
                type_account = self.order.mode.bank_id.state
                if type_account == 'iban':
                    account = account[4:]
                init = account[:8]
                account = init + account[10:]
                text += account
            if (i + 1) == 2:
                street_payer = self.order.mode.bank_id.partner_id.street
                if not street_payer:
                    raise Log(
                        ('Error: Payer %s has not street established. \
                        ') % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(street_payer) < 72:
                        fill = 72 - len(street_payer)
                        street_payer += fill * ' '
                    elif len(street_payer) > 72:
                        street_payer = street_payer[:72]
                    text += street_payer
                street_payer2 = self.order.mode.bank_id.partner_id.street2
                if street_payer2:
                    if len(street_payer2) < 72:
                        fill = 72 - len(street_payer2)
                        street_payer2 += fill * ' '
                    elif len(street_payer2) > 72:
                        street_payer2 = street_payer2[:72]
                    text += street_payer2
            if (i + 1) == 3:
                postalzip = self.order.mode.bank_id.partner_id.zip
                if not postalzip:
                    raise Log(
                        ('Error: Payer %s has not postal zip established. \
                        ') % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(postalzip) < 5:
                        fill = 5 - len(postalzip)
                        postalzip += fill * ' '
                    elif len(postalzip) > 5:
                        postalzip = postalzip[:5]
                    text += postalzip
                city_payer = self.order.mode.bank_id.partner_id.city
                if not city_payer:
                    raise Log(
                        ('Error: Payer %s has not city established. \
                        ') % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(city_payer) < 36:
                        fill = 36 - len(city_payer)
                        city_payer += fill * ' '
                    elif len(city_payer) > 36:
                        city_payer = city_payer[:36]
                    text += city_payer
                state_id = self.order.mode.bank_id.partner_id.state_id.name
                if not state_id:
                    raise Log(
                        ('Error: Payer %s has not state established. \
                        ') % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(state_id) < 25:
                        fill = 25 - len(state_id)
                        state_id += fill * ' '
                    elif len(state_id) > 25:
                        state_id = state_id[:25]
                    text += state_id
            text = text.ljust(90) + '\r\n'
            all_text += text
        return all_text

    def _pop_beneficiary(self, line):
        all_text = ''
        for i in range(3):
            text = '530'
            text += str(i + 1)
            supplier_vat = line['partner_id']['vat']
            supplier_vat = supplier_vat.replace("ES", "")
            if not supplier_vat or len(supplier_vat) > 10:
                raise Log(
                    ('Error: Supplier %s has wrong\
                        VAT.') % line['partner_id']['name'])
            else:
                if len(supplier_vat) < 10:
                    fill = 10 - len(supplier_vat)
                    supplier_vat = (fill * ' ') + supplier_vat
                text += supplier_vat
            if(i + 1) == 1:
                text += 5 * '0'
                ref = self.order.reference
                ref = ref[2:].replace("/", "")
                text += ref.zfill(7)
                supplier_name = line['partner_id']['name']
                if not supplier_name:
                    raise Log(
                        ('Error: Supplier %s has not name established. \
                            ') % line['partner_id']['vat'])
                else:
                    if len(supplier_name) < 40:
                        fill = 40 - len(supplier_name)
                        supplier_name += fill * ' '
                    elif len(supplier_name) > 40:
                        supplier_name = supplier_name[:40]
                    text += supplier_name
                text += self.converter.convert(abs(self.order.total), 10)
                text += datetime.date.today().strftime('%d%m%y')
                if self.order.date_prefered == 'due':
                    planned_date = self.order.line_ids \
                        and self.order.line_ids[0].ml_maturity_date \
                        or datetime.date.today().strftime('%d-%m-%y')
                    planned_date = planned_date.replace('-', '')
                    day = planned_date[6:]
                    month = planned_date[4:6]
                    year = planned_date[2:4]
                    planned_date = day + month + year
                elif self.order.date_prefered == 'now':
                    planned_date = datetime.date.today().strftime('%d%m%y')
                else:
                    planned_date = self.order.date_scheduled
                    if not planned_date:
                        raise Log(
                            ('Error:Planned date not established in order.'))
                    else:
                        planned_date = planned_date.replace('-', '')
                        day = planned_date[6:]
                        month = planned_date[4:6]
                        year = planned_date[:4]
                        planned_date = day + month + year
                text += planned_date
                if self.order.mode.payment_kutxa_type == '56':
                    text += '1'
                else:
                    text += '2'
            if(i + 1) == 2:
                supplier_street = line['partner_id']['street']
                if not supplier_street:
                    raise Log(
                        ('Error: Supplier %s has not \
                            street established.\
                            ') % line['partner_id']['name'])
                else:
                    if len(supplier_street) < 36:
                        fill = 36 - len(supplier_street)
                        supplier_street += fill * ' '
                    elif len(supplier_street) > 36:
                        supplier_street = supplier_street[:36]
                    text += supplier_street
                supplier_street2 = line['partner_id']['street2']
                if supplier_street2:
                    if len(supplier_street2) < 36:
                        fill = 36 - len(supplier_street2)
                        supplier_street2 += fill * ' '
                    elif len(supplier_street2) > 36:
                        supplier_street2 = supplier_street2[:36]
                    text += supplier_street2
            if(i + 1) == 3:
                supplier_zip = line['partner_id']['zip']
                if not supplier_zip:
                    raise Log(
                        ('Error: Supplier %s has not \
                            C.P established.') % line['partner_id']['name'])
                else:
                    if len(supplier_zip) < 5:
                        fill = 5 - len(supplier_zip)
                        supplier_zip += fill * ' '
                    elif len(supplier_zip) > 5:
                        supplier_zip = supplier_zip[:5]
                    text += supplier_zip
                supplier_city = line['partner_id']['city']
                if not supplier_city:
                    raise Log(
                        ('Error: Supplier %s has not \
                            city established.') % line['partner_id']['name'])
                else:
                    if len(supplier_city) < 36:
                        fill = 36 - len(supplier_city)
                        supplier_city += fill * ' '
                    elif len(supplier_city) > 36:
                        supplier_city = supplier_city[:36]
                    text += supplier_city
                supplier_state = line['partner_id']['state_id']['name']
                if not supplier_state:
                    raise Log(
                        ('Error: Supplier %s has not \
                            state established.') % line['partner_id']['name'])
                else:
                    if len(supplier_state) < 15:
                        fill = 15 - len(supplier_state)
                        supplier_state += fill * ' '
                    elif len(supplier_state) > 15:
                        supplier_state = supplier_state[:15]
                    text += supplier_state
                if self.order.mode.payment_kutxa_type == '56':
                    supplier_account = line['bank_id']['acc_number']
                    if not supplier_account:
                        raise Log(
                            ('Error: Supplier %s has not account established. \
                                ') % line['partner_id']['name'])
                    supplier_account = supplier_account.replace(' ', '')
                    type_account = line['bank_id']['state']
                    if type_account == 'iban':
                        supplier_account = supplier_account[4:]
                    init = supplier_account[:8]
                    dc = supplier_account[8:10]
                    supplier_account = init + dc + supplier_account[10:]
                    text += supplier_account
            text = text.ljust(90) + '\r\n'
            all_text += text
        return all_text

    def _pop_detail(self, line):
        text = '560'
        self.number += 1
        text += str(self.number)
        supplier_vat = line['partner_id']['vat']
        supplier_vat = supplier_vat.replace("ES", "")
        if not supplier_vat or len(supplier_vat) > 10:
            raise Log(
                ('Error: Supplier %s has wrong\
                    VAT.') % line['partner_id']['name'])
        else:
            if len(supplier_vat) < 10:
                fill = 10 - len(supplier_vat)
                supplier_vat = (fill * ' ') + supplier_vat
            text += supplier_vat
        under_one = line['communication']
        if under_one:
            if len(under_one) < 36:
                fill = 36 - len(under_one)
                under_one += fill * ' '
            elif len(under_one) > 36:
                under_one = under_one[:36]
            text += under_one
        else:
            text += 36 * ' '
        under_two = line['communication2']
        if under_two:
            if len(under_two) < 36:
                fill = 36 - len(under_two)
                under_two += fill * ' '
            elif len(under_two) > 36:
                under_two = under_two[:36]
            text += under_two
        text = text.ljust(90) + '\r\n'
        return text

    def _pop_totals(self, line):
        text = '5901'
        vat = self.order.mode.bank_id.partner_id.vat
        if not vat:
            raise Log(
                ('Error: VAT of account not established \
                for the account %s.\
                ') % self.order.mode.bank_id.acc_number)
        vat = vat.replace("ES", "")
        if len(vat) < 10:
            fill = 10 - len(vat)
            vat = (fill * ' ') + vat
        elif len(vat) > 10:
            vat = vat[:10]
        text += vat
        text += self.converter.convert(abs(self.order.total), 12)
        num = str(self.num_records)
        text += num.zfill(12)
        total = str((self.num_records * 2) + 6)
        text += total.zfill(12)
        text = text.ljust(90) + '\r\n'
        return text
