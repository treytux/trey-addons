# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import datetime
from openerp import _
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain
from openerp.addons.l10n_es_payment_order.wizard.log import Log


class PaymentCsb68(object):
    def __init__(self, env):
        self.env = env
        self.converter = PaymentConverterSpain()

    def _start_68(self):
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        suffix = self.order.mode.csb_suffix
        return self.converter.convert(vat + suffix, 12)

    def calcule_totals(self, lines):
        total_amount = 0.0
        for line in lines:
            if line['ml_inv_ref'][0].type == 'in_invoice':
                total_amount += abs(line['amount'])
            else:
                total_amount -= abs(line['amount'])
        return self.converter.convert(abs(total_amount), 12)

    def _pop_header(self):
        text = '0359'
        text += self._start_68()
        text += 12 * ' '
        text += '001'
        text += datetime.today().strftime('%d%m%y')
        text += 9 * ' '
        cc = self.order.mode.bank_id.acc_number
        cc = cc.replace(' ', '')
        if len(cc) != 24:
            raise Log(_('Error:Bank account of %s has not set correctly \
                ') % self.order.mode.bank_id.partner_id.name)
        text += cc
        text = text.ljust(100) + '\r\n'
        return text

    def _header_beneficiary_68(self, line):
        text = '0659'
        text += self._start_68()
        text += line['partner_id'].vat.rjust(12)
        return text

    def _get_reference(self, ref, len):
        return ref.replace('/', '').zfill(len)[:len]

    def _pop_beneficiary_headers(self, line, total_payment):
        text = ''
        partner_obj = self.env['res.partner']
        address_ids = line['partner_id'].address_get(['default', 'invoice'])
        if address_ids.get('invoice'):
            address = partner_obj.browse(address_ids.get('invoice'))
        elif address_ids.get('default'):
            address = partner_obj.browse(address_ids.get('default'))
        else:
            raise Log(_('User error:\n\nPartner %s has no invoicing or \
                        default address.') % line['partner_id'].name)
        text1 = self._header_beneficiary_68(line)
        text1 += '010'
        text1 += self.converter.convert(line['partner_id'].name, 40)
        text1 = text1.ljust(100) + '\r\n'
        text += text1
        text2 = self._header_beneficiary_68(line)
        text2 += '011'
        txt_address = ''
        if address.street:
            txt_address += address.street
        if address.street2:
            txt_address += ' ' + address.street2
        text2 += self.converter.convert(txt_address, 45)
        text2 = text2.ljust(100) + '\r\n'
        text += text2
        text3 = self._header_beneficiary_68(line)
        text3 += '012'
        text3 += self.converter.convert(address.zip, 5)
        text3 += self.converter.convert(address.city, 40)
        text3 = text3.ljust(100) + '\r\n'
        text += text3
        text4 = self._header_beneficiary_68(line)
        text4 += '013'
        text4 += self.converter.convert(address.zip, 9)
        text4 += self.converter.convert(address.state_id.name or '', 30)
        text4 += self.converter.convert(address.country_id.name or '', 20)
        text4 = text4.ljust(100) + '\r\n'
        text += text4
        text5 = self._header_beneficiary_68(line)
        text5 += '014'
        ref = line['ml_inv_ref'][0].number
        ref = ''.join([x for x in ref if x.isdigit()])
        self.ref = self._get_reference(ref, 7)
        text5 += self.ref
        self.dc = '9000' + self.ref
        self.dc = int(self.dc) % 7
        self.dc = self.converter.convert(str(self.dc), 1)
        text5 += self.dc
        if line.get('ml_maturity_date'):
            date_pay = datetime.strptime(line['ml_maturity_date'], '%Y-%m-%d')
        elif line.get('date'):
            date_pay = datetime.strptime(line['date'], '%Y-%m-%d')
        else:
            date_pay = datetime.today()
        text5 += self.converter.convert(date_pay.strftime('%d%m%Y'), 8)
        text5 += self.converter.convert(abs(total_payment), 12)
        text5 += '0'
        country_code = address.country_id and address.country_id.code or ''
        if country_code != 'ES':
            text5 += self.converter.convert(country_code, 2)
        else:
            text5 += 2 * ' '
        text5 += 6 * ' '
        text5 = text5.ljust(100) + '\r\n'
        text += text5
        self.num_records += 5
        return text

    def _pop_beneficiary_payment(self, line, num_payment):
        text = ''
        text6 = self._header_beneficiary_68(line)
        text6 += self.converter.convert(abs(num_payment + 15), 3)
        text6 += self.ref
        text6 += self.dc
        text6 += self._get_reference(line['ml_inv_ref'][0].number, 12)
        date_create = datetime.strptime(line['ml_date_created'], '%Y-%m-%d')
        text6 += self.converter.convert(date_create.strftime('%d%m%Y'), 8)
        text6 += self.converter.convert(abs(line['amount']), 12)
        if 'in_invoice' in line['ml_inv_ref'][0].type:
            text6 += 'H'
        else:
            text6 += 'D'
        text6 += self._get_reference(line['ml_inv_ref'][0].number, 9)
        text6 += 2 * ' '
        text6 = text6.ljust(100) + '\r\n'
        text += text6
        self.num_records += 1
        return text

    def _pop_totals(self, lines):
        text = '0859'
        text += self._start_68()
        text += 12 * ' '
        text += 3 * ' '
        text += self.calcule_totals(lines)
        text += self.converter.convert(abs(self.num_records + 2), 10)
        text += 42 * ' '
        text += 5 * ' '
        text = text.ljust(100) + '\r\n'
        return text

    def create_file(self, order, lines):
        self.order = order
        file = ''
        self.num_records = 0
        if self.order.mode.type.code != 'payment_csb_68':
            raise Log(_('Error: Payment mode is not set correctly \
                %s') % self.order.mode.type.code)
        file += self._pop_header()
        partners = {}
        for line in lines:
            dic = partners.setdefault(
                line['partner_id'], {
                    'lines': [],
                    'total_payment': False})
            dic['lines'].append(line)
            if line['ml_inv_ref'][0].type == 'in_invoice':
                dic['total_payment'] += abs(line['amount'])
            else:
                dic['total_payment'] -= abs(line['amount'])
        for partner in partners:
            beneficiary = partners[partner]['lines'][0]
            total_payment = partners[partner]['total_payment']
            file += self._pop_beneficiary_headers(beneficiary, total_payment)
            num_payment = 0
            for line in partners[partner]['lines']:
                file += self._pop_beneficiary_payment(line, num_payment)
                num_payment += 1
        file += self._pop_totals(lines)
        return file
