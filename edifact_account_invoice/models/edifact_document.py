# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
try:
    from bots import botsglobal, botsinit, outmessage
except ImportError:
    import logging
    _log = logging.getLogger(__name__)
    _log.warning('bots python lib not installed.')


class EdifactDocument(models.Model):
    _inherit = 'edifact.document'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')

    @api.multi
    def get_invoice_name(self, name):
        return name.replace('/', '')

    @api.multi
    def get_invoice_date(self, date, dtype='long'):
        date = date.replace('-', '')
        return dtype == 'long' and date[:8] or date[2:8]

    @api.multi
    def get_invoice_time(self, date):
        return date[10:16].replace(':', '')

    @api.multi
    def get_parent_partner(self, partner):
        return partner and partner.parent_id or partner

    @api.multi
    def get_edi_invoice_envelops(self, invoice):
        out = outmessage.outmessage_init(
            editype='edifact', messagetype='INVOICD93AUN',
            filename='1', reference='', statust=2, divtext='')
        out.put({
            'BOTSID': 'UNB',
            'S001.0001': 'UNOC',
            'S001.0002': '3',
            'S002.0004': self.limit_string(
                self.env.ref('base.main_company').company_registry, 17),
            'S002.0007': 'ZZ',
            'S003.0010': '8422416888881',
            'S003.0007': '14',
            'S004.0017': self.get_invoice_date(invoice.write_date, 'short'),
            'S004.0019': self.get_invoice_time(invoice.write_date),
            '0020': self.get_invoice_name(invoice.number)})
        out.put({
            'BOTSID': 'UNB'}, {
                'BOTSID': 'UNZ',
                '0036': '1',
                '0020': self.get_invoice_name(invoice.number)})
        out.messagegrammarread(typeofgrammarfile='envelope')
        out.checkmessage(out.root, out.defmessage)
        out.tree2records(out.root)
        una = 'UNA:+.? \'\n'
        header = out.record2string(out.lex_records[0:1])
        footer = out.record2string(out.lex_records[1:2])
        return una, header, footer

    @api.multi
    def get_edi_invoice_body(self, invoice):
        out = outmessage.outmessage_init(
            editype='edifact', messagetype='INVOICD93AUN',
            filename='1', reference='', statust=2, divtext='')
        ta_info = {
            'sfield_sep': ':',
            'record_tag_sep': '',
            'field_sep': '+',
            'quote_char': '',
            'escape': '?',
            'record_sep': "'",
            'add_crlfafterrecord_sep': '\r\n',
            'forcequote': False,
            'reserve': '*',
            'version': 3}
        out.ta_info.update(ta_info)
        main_company = self.env.ref('base.main_company')
        out.put({
            'BOTSID': 'UNH',
            '0062': self.get_invoice_name(invoice.number),
            'S009.0065': 'DESADV',
            'S009.0052': 'D',
            'S009.0054': '93A',
            'S009.0051': 'UN',
            'S009.0057': 'EAN007'})
        bgm = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'BGM'})
        bgm.put({
            'BOTSID': 'BGM',
            'C002.1001': '380',
            'C002.1000': '2017FVN493',
            'C002.3055': '9'})
        dtm = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'DTM'})
        dtm.put({
            'BOTSID': 'DTM',
            'C507.2005': '137',
            'C507.2380': self.get_invoice_date(invoice.write_date),
            'C507.2379': '102'})
        pai = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'PAI'})
        pai.put({
            'BOTSID': 'PAI',
            'C534.4461': '60'})
        rff = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'ON',
            'C506.1154': self.get_order_number(invoice.origin)})
        rff = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'DQ',
            'C506.1154': self.get_picking(invoice.origin)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        if not main_company.company_registry:
            raise exceptions.Warning(
                _('ERROR: Company %s has no VAT defined: invoice %s')
                % (main_company.name, invoice.number))
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'SCO',
            'C082.3039': self.limit_string(main_company.company_registry, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(main_company.name, 35),
            'C059.3042#1': self.limit_string(main_company.street, 35),
            '3164': self.limit_string(main_company.city, 35),
            '3207': '',
            '3251': self.limit_string(main_company.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(main_company.company_registry, 17)})
        parent_partner = self.get_parent_partner(invoice.partner_id)
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        if not parent_partner.ean13:
            raise exceptions.Warning(
                _('ERROR: Client %s has no EAN defined: invoice %s')
                % (parent_partner.name, invoice.number))
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'BCO',
            'C082.3039': self.limit_string(parent_partner.ean13, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(parent_partner.name, 35),
            'C059.3042#1': self.limit_string(parent_partner.street, 35),
            '3164': self.limit_string(parent_partner.city, 35),
            '3207': '',
            '3251': self.limit_string(parent_partner.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(parent_partner.vat, 17)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'SU',
            'C082.3039': self.limit_string(main_company.company_registry, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(main_company.name, 35),
            'C059.3042#1': self.limit_string(main_company.street, 35),
            '3164': self.limit_string(main_company.city, 35),
            '3207': '',
            '3251': self.limit_string(main_company.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(main_company.company_registry, 17)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'BY',
            'C082.3039': self.limit_string(invoice.partner_id.vat, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(invoice.partner_id.name, 35),
            'C059.3042#1': self.limit_string(invoice.partner_id.street, 35),
            '3164': self.limit_string(invoice.partner_id.city, 35),
            '3207': '',
            '3251': self.limit_string(invoice.partner_id.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(invoice.partner_id.vat, 17)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'API',
            'C506.1154': self.limit_string(invoice.partner_id.ref, 35)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'II',
            'C082.3039': self.limit_string(main_company.company_registry, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(main_company.name, 35),
            'C059.3042#1': self.limit_string(main_company.street, 35),
            '3164': self.limit_string(main_company.city, 35),
            '3207': '',
            '3251': self.limit_string(main_company.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(main_company.company_registry, 17)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'IV',
            'C082.3039': self.limit_string(parent_partner.ean13, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(parent_partner.name, 35),
            'C059.3042#1': self.limit_string(parent_partner.street, 35),
            '3164': self.limit_string(parent_partner.city, 35),
            '3207': '',
            '3251': self.limit_string(parent_partner.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(parent_partner.vat, 17)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'DP',
            'C082.3039': self.limit_string(invoice.partner_id.vat, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(invoice.partner_id.name, 35),
            'C059.3042#1': self.limit_string(invoice.partner_id.street, 35),
            '3164': self.limit_string(invoice.partner_id.city, 35),
            '3207': '',
            '3251': self.limit_string(invoice.partner_id.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(invoice.partner_id.vat, 17)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'PR',
            'C082.3039': self.limit_string(invoice.partner_id.vat, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(invoice.partner_id.name, 35),
            'C059.3042#1': self.limit_string(invoice.partner_id.street, 35),
            '3164': self.limit_string(invoice.partner_id.city, 35),
            '3207': '',
            '3251': self.limit_string(invoice.partner_id.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(invoice.partner_id.vat, 17)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'PE',
            'C082.3039': self.limit_string(main_company.company_registry, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(main_company.name, 35),
            'C059.3042#1': self.limit_string(main_company.street, 35),
            '3164': self.limit_string(main_company.city, 35),
            '3207': '',
            '3251': self.limit_string(main_company.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': self.limit_string(main_company.company_registry, 17)})
        cux = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'CUX'})
        cux.put({
            'BOTSID': 'CUX',
            'C504#1.6347': '2',
            'C504#1.6345': self.limit_string(invoice.currency_id.name, 3),
            'C504#1.6343': '4'})
        pat = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'PAT'})
        pat.put({
            'BOTSID': 'PAT',
            '4279': '35'})
        dtm = pat.putloop({'BOTSID': 'PAT'}, {'BOTSID': 'DTM'})
        dtm.put({
            'BOTSID': 'DTM',
            'C507.2005': '13',
            'C507.2380': self.get_invoice_date(invoice.date_due),
            'C507.2379': '102'})
        count = 1
        total_lines = 0
        for line in invoice.invoice_line:
            total_lines += 1
            lin = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'LIN'})
            lin.put({'BOTSID': 'LIN',
                     '1082': count})
            count += 1
            lin.put({'BOTSID': 'LIN',
                     'C212.7140': line.product_id.ean13 and
                     self.limit_string(line.product_id.ean13, 17) or
                     self.limit_string(line.product_id.default_code, 17),
                     'C212.7143': 'EN'})
            pia = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'PIA'})
            pia.put({'BOTSID': 'PIA',
                     '4347': '1'})
            pia.put({'BOTSID': 'PIA',
                     'C212#1.7140': self.limit_string(
                         line.product_id.default_code, 35),
                     'C212#1.7143': 'IN'})
            pia = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'PIA'})
            pia.put({'BOTSID': 'PIA',
                     '4347': '1'})
            pia.put({'BOTSID': 'PIA',
                     'C212#1.7140': self.limit_string(
                         line.product_id.ean13, 17),
                     'C212#1.7143': 'SA'})
            imd = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'IMD'})
            imd.put({'BOTSID': 'IMD',
                     '7077': 'F',
                     '7081': 'M',
                     'C273.7008#1': self.limit_string(
                         line.product_id.name, 35)})
            qty = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'QTY'})
            qty.put({'BOTSID': 'QTY',
                     'C186.6063': '47',
                     'C186.6060': int(line.quantity)})
            qty = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'QTY'})
            qty.put({'BOTSID': 'QTY',
                     'C186.6063': '46',
                     'C186.6060': int(line.quantity)})
            qty = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'QTY'})
            qty.put({'BOTSID': 'QTY',
                     'C186.6063': '59',
                     'C186.6060': int(line.quantity)})
            moa = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'MOA'})
            moa.put({'BOTSID': 'MOA',
                     'C516.5025': '66',
                     'C516.5004': line.price_subtotal})
            pri = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'PRI'})
            pri.put({'BOTSID': 'PRI',
                     'C509.5125': 'AAA',
                     'C509.5118': line.price_unit})
            pri = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'PRI'})
            pri.put({'BOTSID': 'PRI',
                     'C509.5125': 'AAB',
                     'C509.5118': line.price_unit})
            for prod_tax in line.invoice_line_tax_id:
                tax = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'TAX'})
                tax.put({'BOTSID': 'TAX',
                         '5283': '7',
                         'C241.5153': 'VAT',
                         'C243.5278': self.limit_string(
                             prod_tax.description, 7)})
            taxes = line.invoice_line_tax_id.compute_all(
                line.price_unit, line.quantity)
            moa = tax.putloop({'BOTSID': 'TAX'}, {'BOTSID': 'MOA'})
            moa.put({'BOTSID': 'MOA',
                     'C516.5025': '124',
                     'C516.5004': taxes['taxes'][0]['amount']})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'UNS',
                '0081': 'S'})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'CNT',
                'C270.6069': '2',
                'C270.6066': total_lines})

        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'MOA',
                'C516.5025': '79',
                'C516.5004': invoice.amount_untaxed})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'MOA',
                'C516.5025': '98',
                'C516.5004': invoice.amount_untaxed})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'MOA',
                'C516.5025': '125',
                'C516.5004': invoice.amount_untaxed})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'MOA',
                'C516.5025': '139',
                'C516.5004': invoice.amount_total})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'MOA',
                'C516.5025': '179',
                'C516.5004': invoice.amount_tax})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'TAX',
                'BOTSIDnr': '2',
                '5283': '7',
                'C241.5153': 'VAT',
                'C243.5278': self.limit_string(prod_tax.description, 7)})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'MOA',
                'C516.5025': '179',
                'C516.5004': invoice.amount_tax})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'MOA',
                'C516.5025': '125',
                'C516.5004': invoice.amount_untaxed})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'UNT',
                '0074': out.getcount() + 1,
                '0062': self.get_invoice_name(invoice.number)})
        out.writeall()
        return out.record2string(out.lex_records)

    @api.multi
    def compose_edi_invoice(self, invoice):
        configdir = 'config'
        botsinit.generalinit(configdir)
        process_name = 'odoo_get_edi'
        botsglobal.logger = botsinit.initenginelogging(process_name)
        una, header, footer = self.get_edi_invoice_envelops(invoice)
        body = self.get_edi_invoice_body(invoice)
        content = ''.join([una, header, body, footer])
        return content

    @api.multi
    def process_invoice_out_files(self, invoices):
        edi_doc = False
        for invoice in invoices:
            content = self.compose_edi_invoice(invoice)
            inv_name = self.get_invoice_name(invoice.number)
            edi_doc = self.create({
                'name': inv_name,
                'ttype': 'invoice',
                'import_log': ''})
            try:
                file_path = self.write_out_file('invoices', '.'.join(
                    [inv_name, 'edi']), content)
            except IOError:
                edi_doc.import_log = '\n'.join([edi_doc.import_log, _(
                    'Cannot export: %s. File Structure Error: %s') % (
                        invoice.name, _(
                            'See if out path is defined in Settings / '
                            'Companies / Companies > Configuration > EDI '
                            'Parameters > Out path. Inside this path, you must'
                            ' have a directory called \'invoices\'.'))])
                edi_doc.state = 'error'
                continue
            except Exception as e:
                edi_doc.import_log = '\n'.join([
                    edi_doc.import_log,
                    _('Cannot export: %s. Error: %s') %
                    (invoice.name, str(e.args))])
                edi_doc.state = 'error'
                continue
            invoice.edi_doc_id = edi_doc.id
            edi_doc.state = 'exported'
            edi_doc.file_name = file_path
            edi_doc.invoice_id = invoice.id
            edi_doc.import_log = '\n'.join(
                [edi_doc.import_log, 'OK: %s' % invoice.number])
        return edi_doc

    @api.one
    def export_invoice_again(self):
        return self.process_invoice_out_files([self.invoice_id])
