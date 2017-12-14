# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from odoocli import client, struct, parser, origin
import sys
import os
import logging
_log = logging.getLogger('MIGRATE')

struct.Csv._float_decimal_separator = ','
struct.Csv._float_thousand_separator = '.'
struct.Csv._date_format = '%d-%m-%y'


class PartnerCategory(struct.Csv):

    _from = 'raya_dental_partner_category.txt'
    _first_row_titles = True
    _default_record = {
    }
    _initialized = False

    _map = [
        parser.Str(src='name', dst='name'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
    ]

    def to(self):
        for category in self.read():  # (count=200):
            try:
                c = self.env['res.partner.category'].create(category.dict())
            except Exception as e:
                _log.error('User data %s' % category.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('User "%s" imported with id %s' % (
                category.name, c.id))


class Partner(struct.Csv):

    _PAY_MODE = {
        "10": "Giro",
        "15": "Giro",
        "1G": "Giro",
        "1V": "Giro",
        "2G": "Giro",
        "3G": "Giro",
        "4G": "Giro",
        "5V": "Giro",
        "90": "Giro",
        "AL": "A La Vista +1000E x2G",
        "AV": "A La Vista",
        "CO": "Recibo",
        "CR": "ContraReembolso",
        "CX": "[*] Efectivo",
        "DB": "Domiciliado",
        "EF": "Efectivo",
        "EM": "eMail",
        "ET": "Talon/Cheque",
        "F0": "Financiado",
        "GI": "Giro Postal",
        "TA": "Pagare",
        "TB": "Transferencia CajaSur",
        "TR": "Transferencia Santander",
        "TV": "Tarjeta Credito",
    }
    _PAY_TERM = {
        "10": "39 Dias",
        "15": "15 Dias",
        "1G": "30 Dias",
        "1V": "60 Dias",
        "2G": "30/60 Dias",
        "3G": "30/60/90 Dias",
        "4G": "30/60/90/120 Dias",
        "5V": "30/60/90/120/180 Dias",
        "90": "90 Dias",
        "AL": "nmediato",
        "AV": "nmediato",
        "CO": "nmediato",
        "CR": "nmediato",
        "CX": "nmediato",
        "DB": "5 Dias",
        "EF": "nmediato",
        "EM": "nmediato",
        "ET": "nmediato",
        "F0": "12 Meses",
        "GI": "nmediato",
        "TA": "nmediato",
        "TB": "nmediato",
        "TR": "nmediato",
        "TV": "nmediato"
    }

    _from = 'raya_dental_partner.txt'
    _first_row_titles = True
    _default_record = {
        'comment': '',
        'is_company': True,
        'vat_subjected': True,
    }
    _initialized = False

    _map = [
        parser.Custom(src='customer', dst='customer', parser='parser_boolean'),
        parser.Custom(src='supplier', dst='supplier', parser='parser_boolean'),
        parser.Str(src='ref', dst='ref'),
        parser.Str(src='name', dst='name'),
        parser.Str(src='comercial', dst='comercial'),
        parser.Custom(src='category_id', dst='category_id',
                      parser='parser_category_id'),
        parser.Vat(src='vat', dst='vat'),
        parser.Str(src='street', dst='street'),
        parser.Str(src='city', dst='city'),
        parser.Str(src='state_id', dst='state_id'),
        parser.Str(src='country', dst='country_id'),
        parser.Custom(src='zip', dst='zip', parser='parser_zip'),
        parser.Str(src='phone', dst='phone'),
        parser.Str(src='mobile', dst='mobile'),
        parser.Str(src='fax', dst='fax'),
        parser.Str(src='email', dst='email'),
        parser.Str(src='web', dst='website'),
        parser.Date(src='date', dst='date'),
        parser.Custom(src='user_id', dst='user_id', parser='parser_user_id'),
        parser.Custom(src='property_account_position',
                      dst='property_account_position',
                      parser='parser_property_account_position'),
        parser.Custom(src='property_account_receivable',
                      dst='property_account_receivable',
                      parser='parser_property_account_receivable'),
        parser.Custom(src='customer_payment_mode_code',
                      dst='customer_payment_mode',
                      parser='parser_customer_payment_mode'),
        parser.Float(src='credit', dst='credit'),
        parser.Custom(src='property_account_payable',
                      dst='property_account_payable',
                      parser='parser_property_account_payable'),
        parser.Custom(src='supplier_payment_mode_code',
                      dst='supplier_payment_mode',
                      parser='parser_supplier_payment_mode'),
        parser.Custom(src='comment', dst='comment', parser='parser_comment'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
    ]

    def parser_comment(self, value):
        value = value.strip()
        self.record.comment = value or ''

    def parser_boolean(self, value):
        value = value.strip()
        if value == 'S':
            return True
        else:
            return False

    def parser_category_id(self, value):
        value = value.strip()
        categorys = value.split(',')
        result = []
        for category in categorys:
            category_ids = self.env['res.partner.category'].search([
                ('name', '=', category)])
            if category_ids:
                result.append(category_ids[0].id)
                self.record.category_id = categorys[0]
        if result:
            self.record.category_id = [(6, 0, result)]
        else:
            self.record.category_id = None

    def parser_user_id(self, value):
        value = value.strip()
        users = self.env['res.users'].search([('name', '=', value)])
        if users:
            self.record.user_id = users[0]
        else:
            self.record.user_id = None

    def parser_zip(self, value):
        value = value.strip()
        zips = self.env['res.better.zip'].search([('name', '=', value)])
        if zips:
            self.record.zip_id = zips[0].id or None
            self.record.zip = zips[0].name or None
            self.record.city = zips[0].city or None
            self.record.state_id = zips[0].state_id.id or None
            self.record.country_id = zips[0].country_id.id or None
        else:
            self.record.comment += 'Direccion\n=========\n%s\n%s \n' % (
                self.record.get('street', ''), value)
            self.record.comment += 'Codigo postal\n=========\n%s\n%s \n' % (
                self.record.get('zip', ''), value)
            self.record.comment += 'Poblacion\n=========\n%s\n%s \n' % (
                self.record.get('city', ''), value)
            self.record.comment += 'Provincia\n=========\n%s\n%s \n' % (
                self.record.get('state_id', ''), value)
            self.record.comment += 'Pais\n=========\n%s\n%s \n' % (
                self.record.get('country_id', ''), value)
            self.record.zip_id = None
            self.record.state_id = None
            self.record.country_id = None

    def parser_property_account_position(self, value):
        value = value.strip()
        account_positions = self.env['account.fiscal.position'].search([
            ('name', '=', value)])
        if account_positions:
            self.record.property_account_position = account_positions[0].id
        else:
            self.record.comment += 'Posicion Fiscal\n=========\n%s\n%s \n' % (
                self.record.get('property_account_position', ''), value)

    def parser_property_account_receivable(self, value):
        value = value.strip()
        if value == "":
            value = '430000000'
        accounts = self.env['account.account'].search([
            ('code', '=', value)])
        if accounts:
            self.record.property_account_receivable = accounts[0].id
        else:
            self.record.property_account_receivable = None

    def parser_property_account_payable(self, value):
        value = value.strip()
        if value == "":
            value = '400000000'
        accounts = self.env['account.account'].search([
            ('code', '=', value)])
        if accounts:
            self.record.property_account_payable = accounts[0].id
        else:
            self.record.property_account_payable = None

    def parser_customer_payment_mode(self, value):
        value = value.strip()
        if value:
            mode = self._PAY_MODE[value] or None
            term = self._PAY_TERM[value] or None
            payment_modes = self.env['payment.mode'].search([
                ('name', '=', mode)])
            payment_terms = self.env['account.payment.term'].search([
                ('name', '=', term)])
            if payment_modes:
                self.record.customer_payment_mode = payment_modes[0].id
            else:
                self.record.customer_payment_mode = None

            if payment_terms:
                self.record.property_payment_term = payment_terms[0].id
            else:
                self.record.property_payment_term = None

    def parser_supplier_payment_mode(self, value):
        value = value.strip()
        if value:
            mode = self._PAY_MODE[value] or None
            term = self._PAY_TERM[value] or None

            payment_modes = self.env['payment.mode'].search([
                ('name', '=', mode)])
            payment_terms = self.env['account.payment.term'].search([
                ('name', '=', term)])

            if payment_modes:
                self.record.supplier_payment_mode = payment_modes[0].id
            else:
                self.record.supplier_payment_mode = None
            if payment_terms:
                self.record.property_supplier_payment_term = payment_terms[
                    0].id
            else:
                self.record.property_supplier_payment_term = None

    def to(self):
        for partner in self.read():  # (count=200):
            try:
                p = self.env['res.partner'].create(partner.dict())
            except Exception as e:
                _log.error('User data %s' % partner.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('Partner "%s" imported with id %s' % (
                partner.name, p.id))


class Contact(struct.Csv):
    _from = 'raya_dental_partner_contact.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Custom(src='ref', dst='parent_id', parser='parser_parent'),
        parser.Str(src='type', dst='type'),
        parser.Str(src='name', dst='name'),
        parser.Str(src='function', dst='function'),
        parser.Str(src='street', dst='street'),
        parser.Str(src='city', dst='city'),
        parser.Custom(src='zip', dst='zip', parser='parser_zip'),
        parser.Str(src='phone', dst='phone'),
        parser.Str(src='mobile', dst='mobile'),
        parser.Str(src='email', dst='email'),
        parser.Date(src='date', dst='date'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
    ]

    def parser_parent(self, value):
        value = value.strip()
        parents = self.env['res.partner'].search([
            ('ref', '=', value)])
        if parents:
            self.record.parent_id = parents[0].id
        else:
            self.record.parent_id = None

    def parser_zip(self, value):
        value = value.strip()
        zips = self.env['res.better.zip'].search([('name', '=', value)])
        if zips:
            self.record.zip_id = zips[0].id or None
            self.record.zip = zips[0].name or None
            self.record.city = zips[0].city or None
            self.record.state_id = zips[0].state_id.id or None
            self.record.country_id = zips[0].country_id.id or None
        else:
            self.record.zip_id = None
            self.record.state_id = None
            self.record.country_id = None

    def to(self):
        for contact in self.read():  # (count=200):
            try:
                c = self.env['res.partner'].create(contact.dict())
            except Exception as e:
                _log.error('User data %s' % contact.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('Contact "%s" imported with id %s' % (
                contact.name, c.id))


class PartnersBank(struct.Csv):
    _from = 'raya_dental_partner_bank.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Str(src='partner_id', dst='bank_name'),
        parser.Str(src='state', dst='state'),
        parser.Custom(src='country', dst='country_id',
                      parser='parser_country'),
        parser.Custom(src='acc_number', dst='acc_number',
                      parser='parser_acc_number'),
        parser.Str(src='bank_bic', dst='bank_bic'),
        parser.Custom(src='partner_id', dst='partner_id',
                      parser='parser_partner'),

    ]

    def parser_country(self, value):
        value = value.strip()
        countrys = self.env['res.country'].search([('code', '=', value)])
        if countrys:
            self.record.acc_country_id = countrys[0].id or None
        else:
            self.record.acc_country_id = None

    def parser_partner(self, value):
        value = value.strip()
        partners = self.env['res.partner'].search([('ref', '=', value)])
        if partners:
            self.record.partner_id = partners[0].id
        else:
            self.record.partner_id = None

    def parser_acc_number(self, value):
        value = value.strip()
        cc_code = value[4:8]
        banks = self.env['res.bank'].search([('code', '=', cc_code)])
        self.record.bank = banks and banks[0].id or None,
        self.record.bank_name = banks and [banks[0].name][0] or '',
        self.record.acc_country_id = banks and banks[0].country.id or None,
        self.record.acc_number = value

    def to(self):
        for bank_account in self.read():  # (count=200):
            try:
                bc = self.env['res.partner.bank'].create(bank_account.dict())
            except Exception as e:
                _log.error('User data %s' % bank_account.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('Bank Account "%s" imported with id %s partner %s' % (
                bank_account.acc_number, bc.id, bank_account.partner_id))


# -----------------------------------------------------------------------------
#                                   MAIN
# -----------------------------------------------------------------------------
def get_path(*relative_path):
    fname = os.path.join(__file__, '../../../../..', *relative_path)
    return os.path.abspath(fname)


def test_before_init(env, company_ref):
    company = env.ref(company_ref)
    periods = env['account.period'].search(
        [('special', '=', True), ('company_id', '=', company.id)])
    if not periods:
        return 'No existen periodos de asiento de apertura para "%s"' % (
            company.name)

    accounts = env['account.account'].search([('company_id', '=', company.id)])
    if not accounts:
        return ('No existen cuentas contables para "%s", ¿esta cargado '
                'el PGE?' % company.name)

    journals = env['account.journal'].search(
        [('type', '=', 'situation'), ('company_id', '=', company.id)])
    if not journals:
        return ('No existen diarios de apertura para "%s"' % company.name)

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Añada el nombre de la base de datos por ejemplo:'
        print '   python %s BASE_DE_DATOS' % sys.argv[0]
        print ''
        sys.exit()
    dbname = sys.argv[1:][:1][0]

    odoo = client(
        path=get_path('server'),
        args='-c %s -d %s' % (
            get_path('instances', 'trey', 'openerp-server.conf'),
            dbname))
    csv = origin.Csv(
        path=get_path(
            'addons',
            'custom',
            'raya_customize',
            'migrate',
            'data'),
        delimiter=';',
        charset='utf-8')

    # *************************************************************
    #                      CARGA DE CATEGORIAS DE PARTNER
    # *************************************************************

    _log = logging.getLogger('MIGRATE::PartnerCategory')
    _log.info('=' * 100)
    _log.info('Category')
    PartnerCategory(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                      CARGA DE PARTNERS
    # *************************************************************

    _log = logging.getLogger('MIGRATE::Partner')
    _log.info('=' * 100)
    _log.info('Partner')
    Partner(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                      CARGA DE CONTACTOS
    # *************************************************************

    _log = logging.getLogger('MIGRATE::Contact')
    _log.info('=' * 100)
    _log.info('Contact')
    Contact(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                      CARGA DE BANCOS DE PARTNERS
    # *************************************************************

    _log = logging.getLogger('MIGRATE::PartnersBank')
    _log.info('=' * 100)
    _log.info('PartnersBank')
    PartnersBank(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                           GENERAL
    # *************************************************************

    _log = logging.getLogger('MIGRATE')
    _log.info('=' * 100)
    _log.info('Commiting data')
    odoo.commit()
    odoo.close()
