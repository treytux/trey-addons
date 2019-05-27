# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain
from openerp.addons.l10n_es_payment_order.wizard.log import Log
import datetime


class ConfirmingKutxa(object):
    def __init__(self, env):
        self.env = env
        self.converter = PaymentConverterSpain()

    def create_file(self, order, lines):
        self.order = order
        self.num_records = 0
        self.total = 0
        if self.order.mode.type.code == 'conf_kutxa':
            txt_file = self._pop_header()
            for line in lines:
                txt_file += self._pop_beneficiary(line)
                txt_file += self._pop_detail(line)
                self.num_records += 1
                if line['ml_inv_ref'][0].type == 'in_invoice':
                    self.total += line['amount']
                else:
                    self.total -= line['amount']
            txt_file += self._pop_totals(line, self.num_records)
        return txt_file

    def _pop_header(self):
        if self.order.date_prefered == 'due':
            planned_date = self.order.line_ids \
                and self.order.line_ids[0].ml_maturity_date \
                or datetime.date.today().strftime('%Y-%d-%m')
            planned_date = planned_date.replace('-', '')
            day = planned_date[6:]
            month = planned_date[4:6]
            year = planned_date[0:4]
            planned_date = year + month + day
        elif self.order.date_prefered == 'now':
            planned_date = datetime.date.today().strftime('%Y%m%d')
        else:
            planned_date = self.order.date_scheduled
            if not planned_date:
                raise Log(
                    ("Error: Planned date not established in pay order."))
            else:
                planned_date = planned_date.replace('-', '')
                day = planned_date[6:]
                month = planned_date[4:6]
                year = planned_date[:4]
                planned_date = day + month + year
        all_text = ''
        for i in range(2):
            text = ''
            text += str(i + 1)
            if (i + 1) == 1:
                payer = self.order.mode.bank_id.partner_id.name
                if not payer:
                    raise Log(
                        ("Error: Owner of account not established \
                        for the account %s.\
                        ") % self.order.mode.bank_id.acc_number)
                if len(payer) <= 50:
                    fill = 50 - len(payer)
                    payer += fill * ' '
                elif len(payer) > 50:
                    payer = payer[:50]
                text += payer
                vat = self.order.mode.bank_id.partner_id.vat.replace('ES', '')
                if len(vat) <= 15:
                    fill = 15 - len(vat)
                    vat += fill * ' '
                elif len(vat) > 15:
                    vat = vat[:15]
                text += vat
                text += planned_date
                text += datetime.date.today().strftime('%Y%m%d')
                contract_number = str(self.order.mode.contract_number)
                if len(contract_number) <= 20:
                    contract_number = contract_number.rjust(20)
                elif len(contract_number) > 20:
                    contract_number = contract_number[-20:]
                text += contract_number
                account = self.order.mode.bank_id.acc_number
                account = account.replace(' ', '')
                if len(account) <= 34:
                    fill = 34 - len(account)
                    account += fill * ' '
                text += account
                text += '978'
                text += '1'
                ref = self.order.mode.type.code
                ref += self.order.reference
                ref = ref.replace('/', '').replace('_', '')
                if len(ref) <= 30:
                    fill = 30 - len(ref)
                    ref += fill * ' '
                elif len(ref) > 30:
                    ref = ref[-30:]
                text += ref
                text += 'FU'
            if (i + 1) == 2:
                street_payer = self.order.mode.bank_id.partner_id.street
                if not street_payer:
                    raise Log(
                        ("Error: Payer %s has not street established. \
                        ") % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(street_payer) < 65:
                        fill = 65 - len(street_payer)
                        street_payer += fill * ' '
                    elif len(street_payer) > 65:
                        street_payer = street_payer[:65]
                    text += street_payer
                city_payer = self.order.mode.bank_id.partner_id.city
                if not city_payer:
                    raise Log(
                        ("Error: Payer %s has not city established. \
                        ") % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(city_payer) < 40:
                        fill = 40 - len(city_payer)
                        city_payer += fill * ' '
                    elif len(city_payer) > 40:
                        city_payer = city_payer[:40]
                    text += city_payer
                postalzip = self.order.mode.bank_id.partner_id.zip
                if not postalzip:
                    raise Log(
                        ("Error: Payer %s has not postal zip established. \
                        ") % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(postalzip) < 10:
                        fill = 10 - len(postalzip)
                        postalzip += fill * ' '
                    elif len(street_payer) > 10:
                        street_payer = street_payer[:10]
                    text += postalzip
            text = text.ljust(250) + '\r\n'
            all_text += text
        return all_text

    def _pop_beneficiary(self, line):
        all_text = ''
        for i in range(3):
            text = ''
            text += str(i + 3)
            if(i + 1) == 1:
                supplier_name = line['partner_id']['name']
                if not supplier_name:
                    raise Log(
                        ("Error: Supplier %s has not name established. \
                            ") % line['partner_id']['vat'])
                else:
                    if len(supplier_name) < 70:
                        fill = 70 - len(supplier_name)
                        supplier_name += fill * ' '
                    elif len(supplier_name) > 70:
                        supplier_name = supplier_name[:70]
                    text += supplier_name
                supplier_vat = line['partner_id']['vat']
                if not supplier_vat or len(supplier_vat) > 20:
                    raise Log(
                        ("Error: Supplier %s has wrong\
                            VAT.") % line['partner_id']['name'])
                else:
                    if len(supplier_vat) < 20:
                        fill = 20 - len(supplier_vat)
                        supplier_vat += fill * ' '
                    text += supplier_vat
                supplier_street = line['partner_id']['street']
                if not supplier_street:
                    raise Log(
                        ("Error: Supplier %s has not \
                            street established.\
                            ") % line['partner_id']['name'])
                else:
                    if len(supplier_street) < 65:
                        fill = 65 - len(supplier_street)
                        supplier_street += fill * ' '
                    elif len(supplier_street) > 65:
                        supplier_street = supplier_street[:65]
                    text += supplier_street
                supplier_city = line['partner_id']['city']
                if not supplier_city:
                    raise Log(
                        ("Error: Supplier %s has not \
                            city established.") % line['partner_id']['name'])
                else:
                    if len(supplier_city) < 40:
                        fill = 40 - len(supplier_city)
                        supplier_city += fill * ' '
                    elif len(supplier_city) > 40:
                        supplier_city = supplier_city[:40]
                    text += supplier_city
                supplier_zip = line['partner_id']['zip']
                if not supplier_zip:
                    raise Log(
                        ("Error: Supplier %s has not \
                            C.P established.") % line['partner_id']['name'])
                else:
                    if len(supplier_zip) < 10:
                        fill = 10 - len(supplier_zip)
                        supplier_zip += fill * ' '
                    elif len(supplier_zip) > 10:
                        supplier_zip = supplier_zip[:10]
                    text += supplier_zip
                text += 'ES'
            if(i + 1) == 2:
                supplier_mail = line['partner_id']['email']
                if not supplier_mail or len(supplier_mail) > 50:
                    raise Log(
                        ("Error: Supplier %s has wrong \
                            Email") % line['partner_id']['name'])
                else:
                    if len(supplier_mail) < 50:
                        fill = 50 - len(supplier_mail)
                        supplier_mail += fill * ' '
                    text += supplier_mail
                text += 50 * ' '
                supplier_phone = line['partner_id']['phone']
                if not supplier_phone or len(supplier_phone) > 15:
                    text += 15 * ' '
                else:
                    if len(supplier_phone) < 15:
                        fill = 15 - len(supplier_phone)
                        supplier_phone += fill * ' '
                    text += supplier_phone
                supplier_fax = line['partner_id']['fax']
                if not supplier_fax or len(supplier_fax) > 15:
                    text += 15 * ' '
                else:
                    if len(supplier_fax) < 15:
                        fill = 15 - len(supplier_fax)
                        supplier_fax += fill * ' '
                    text += supplier_fax
            if(i + 1) == 3:
                if self.order.mode.conf_kutxa_type == '56':
                    text += 'T'
                    supplier_account = line['bank_id']['acc_number']
                    if not supplier_account:
                        raise Log(
                            ("Error: Supplier %s has not account established. \
                                ") % line['partner_id']['name'])
                    supplier_account = supplier_account.replace(' ', '')
                    if len(supplier_account) < 34:
                        fill = 34 - len(supplier_account)
                        supplier_account += fill * ' '
                    text += supplier_account
                elif self.order.mode.conf_kutxa_type == '57':
                    text += 'C'
                    text += 34 * ' '
                text += 11 * ' '
                text += 34 * ' '
                text += 'ES'
            text = text.ljust(250) + '\r\n'
            all_text += text
        return all_text

    def _pop_detail(self, line):
        text = ''
        text += '6'
        invoice_number = line['ml_inv_ref'][0]['number']
        if not invoice_number:
            raise Log(
                ("Error: Invoice %s has not \
                    valid invoice number.") % line['partner_id']['name'])
        invoice_number = invoice_number.replace('-', '')
        if len(invoice_number) < 20:
            fill = 20 - len(invoice_number)
            invoice_number += fill * ' '
        elif len(invoice_number) > 20:
            invoice_number = invoice_number[-20:]
        text += invoice_number
        if line['ml_inv_ref'][0].type == 'in_invoice':
            text += '-'
        else:
            text += '+'
        invoice_amount = self.converter.convert(abs(line['amount']), 15)
        text += invoice_amount
        invoice_date = line['ml_inv_ref'][0][
            'date_invoice'].replace('-', '')
        day = invoice_date[6:]
        month = invoice_date[4:6]
        year = invoice_date[:4]
        invoice_date = year + month + day
        text += invoice_date
        invoice_expiration = line['ml_inv_ref'][0][
            'date_due'].replace('-', '')
        day = invoice_expiration[6:]
        month = invoice_expiration[4:6]
        year = invoice_expiration[:4]
        invoice_expiration = year + month + day
        text += invoice_expiration
        text += 8 * ' '
        if line['ml_inv_ref'][0]['reference']:
            invoice_ref = line['ml_inv_ref'][0][
                'reference'].replace('-', '')
            if len(invoice_ref) < 16:
                fill = 16 - len(invoice_ref)
                invoice_ref += fill * ' '
            elif len(invoice_ref) > 16:
                invoice_ref = invoice_ref[:16]
            text += invoice_ref
        else:
            text += 16 * ' '
        text = text.ljust(250) + '\r\n'
        return text

    def _pop_totals(self, line, num_records):
        text = ''
        text += '7'
        num = str(num_records)
        text += num.zfill(12)
        text += self.converter.convert(abs(self.total), 15)
        text = text.ljust(250) + '\r\n'
        return text
