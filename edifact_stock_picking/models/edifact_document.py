# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _, exceptions
try:
    from bots import botsglobal, botsinit, outmessage

except ImportError:
    import logging
    _log = logging.getLogger(__name__)
    _log.warning('bots python lib not installed.')


class EdifactDocument(models.Model):
    _inherit = 'edifact.document'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking')

    @api.multi
    def get_picking_name(self, name):
        return name.replace('/', '')

    @api.multi
    def get_picking_date(self, date):
        return date[:10].replace('-', '')

    @api.multi
    def get_picking_time(self, date):
        return date[10:16].replace(':', '')

    @api.multi
    def get_edi_picking_envelops(self, picking):
        out = outmessage.outmessage_init(
            editype='edifact', messagetype='DESADVD96AUNEAN',
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
            'S004.0017': self.get_picking_date(picking.date),
            'S004.0019': self.get_picking_time(picking.date),
            '0020': self.get_picking_name(picking.name)})
        out.put({
            'BOTSID': 'UNB'}, {
                'BOTSID': 'UNZ',
                '0036': '1',
                '0020': self.get_picking_name(picking.name)})
        out.messagegrammarread(typeofgrammarfile='envelope')
        out.checkmessage(out.root, out.defmessage)
        out.tree2records(out.root)
        una = 'UNA:+.? \'\n'
        header = out.record2string(out.lex_records[0:1])
        footer = out.record2string(out.lex_records[1:2])
        return una, header, footer

    @api.multi
    def get_edi_picking_body(self, picking):
        out = outmessage.outmessage_init(
            editype='edifact', messagetype='DESADVD96AUNEAN005',
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
            '0062': self.get_picking_name(picking.name),
            'S009.0065': 'DESADV',
            'S009.0052': 'D',
            'S009.0054': '96A',
            'S009.0051': 'UN',
            'S009.0057': 'EAN005'})
        bgm = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'BGM'})
        bgm.put({
            'BOTSID': 'BGM',
            'C002.1001': '351',
            'C002.1000': '1700705',
            'C002.3055': '9'})
        dtm = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'DTM'})
        dtm.put({
            'BOTSID': 'DTM',
            'C507.2005': '137',
            'C507.2380': self.get_picking_date(picking.date),
            'C507.2379': '102'})
        ali = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'ALI'})
        ali.put({
            'BOTSID': 'ALI',
            '4183#1': 'X6'})
        rff = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'ON',
            'C506.1154': self.get_order_number(picking.origin)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        if not main_company.company_registry:
            raise exceptions.Warning(
                _('ERROR: Company %s has no VAT defined: picking %s')
                % (main_company.name, picking.name))
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'MS',
            'C082.3039': self.limit_string(main_company.company_registry, 35),
            'C082.3055': '9'})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        if not picking.partner_id.ean13:
            raise exceptions.Warning(
                _('ERROR: Client %s has no EAN defined: picking %s')
                % (picking.partner_id.name, picking.name))
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'MR',
            'C082.3039': self.limit_string(picking.partner_id.ean13, 17),
            'C082.3055': '9'})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'SU',
            'C082.3039': self.limit_string(main_company.company_registry, 35),
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
            'C506.1154': self.limit_string(main_company.company_registry, 35)})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'BY',
            'C082.3039': self.limit_string(picking.partner_id.ean13, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(picking.partner_id.name, 35),
            'C059.3042#1': self.limit_string(picking.partner_id.street, 35),
            '3164': self.limit_string(picking.partner_id.city, 35),
            '3207': '',
            '3251': self.limit_string(picking.partner_id.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'API',
            'C506.1154': '513'})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': picking.partner_id.vat and
            self.limit_string(picking.partner_id.vat, 35) or ''})
        nad = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'NAD'})
        nad.put({
            'BOTSID': 'NAD',
            '3035': 'DP',
            'C082.3039': self.limit_string(picking.partner_id.ean13, 17),
            'C082.3055': '9',
            'C080.3036#1': self.limit_string(picking.partner_id.name, 35),
            'C059.3042#1': self.limit_string(picking.partner_id.street, 35),
            '3164': self.limit_string(picking.partner_id.city, 35),
            '3207': '',
            '3251': self.limit_string(picking.partner_id.zip, 9)})
        rff = nad.putloop({'BOTSID': 'NAD'}, {'BOTSID': 'RFF'})
        rff.put({
            'BOTSID': 'RFF',
            'C506.1153': 'VA',
            'C506.1154': picking.partner_id.vat and
            self.limit_string(picking.partner_id.vat, 35) or ''})
        cps = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'CPS'})
        cps.put({
            'BOTSID': 'CPS',
            '7164': '1'})
        pac = cps.putloop({'BOTSID': 'CPS'}, {'BOTSID': 'PAC'})
        pac.put({
            'BOTSID': 'PAC',
            '7224': '1'})
        cps = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'CPS'})
        cps.put({
            'BOTSID': 'CPS',
            '7164': '2',
            '7166': '1'})
        pac = cps.putloop({'BOTSID': 'CPS'}, {'BOTSID': 'PAC'})
        pac.put({
            'BOTSID': 'PAC',
            '7224': '1',
            'C202.7065': '201'})
        pci = pac.putloop({'BOTSID': 'PAC'}, {'BOTSID': 'PCI'})
        pci.put({
            'BOTSID': 'PCI',
            '4233': '33E'})
        gin = pci.putloop({'BOTSID': 'PCI'}, {'BOTSID': 'GIN'})
        gin.put({
            'BOTSID': 'GIN',
            '7405': 'BJ',
            'C208#1.7402#1': '300000000000014282'})
        cps_lin = out.putloop({'BOTSID': 'UNH'}, {'BOTSID': 'CPS'})
        cps_lin.put({'BOTSID': 'CPS',
                     '7164': '3',
                     '7166': '2'})
        pac = cps_lin.putloop({'BOTSID': 'CPS'}, {'BOTSID': 'PAC'})
        pac.put({'BOTSID': 'PAC',
                 '7224': '1',
                 'C531.7233': '52',
                 'C202.7065': 'CT'})
        pci = pac.putloop({'BOTSID': 'PAC'}, {'BOTSID': 'PCI'})
        pci.put({'BOTSID': 'PCI',
                 '4233': '33E'})
        gin = pci.putloop({'BOTSID': 'PCI'}, {'BOTSID': 'GIN'})
        gin.put({'BOTSID': 'GIN',
                 '7405': 'BJ',
                 'C208#1.7402#1': '300000000000014299'})
        count = 1
        total_qty = 0
        for move in picking.move_lines:
            total_qty += move.product_uom_qty
            lin = cps_lin.putloop({'BOTSID': 'CPS'}, {'BOTSID': 'LIN'})
            lin.put({'BOTSID': 'LIN',
                     '1082': count})
            count += 1
            lin.put({'BOTSID': 'LIN',
                     'C212.7140': move.product_id.ean13 and
                     self.limit_string(move.product_id.ean13, 35) or (
                         self.limit_string(move.product_id.default_code, 35)),
                     'C212.7143': 'EN'})
            pia = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'PIA'})
            pia.put({'BOTSID': 'PIA',
                     '4347': '1'})
            pia.put({'BOTSID': 'PIA',
                     'C212#1.7140': self.limit_string(
                         move.product_id.default_code, 35),
                     'C212#1.7143': 'IN'})
            pia = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'PIA'})
            pia.put({'BOTSID': 'PIA',
                     '4347': '1'})
            pia.put({'BOTSID': 'PIA',
                     'C212#1.7140': self.limit_string(
                         move.product_id.ean13, 17),
                     'C212#1.7143': 'SA'})
            imd = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'IMD'})
            imd.put({'BOTSID': 'IMD',
                     '7077': 'F',
                     'C273.3055': '9',
                     'C273.7008#1': self.limit_string(
                         move.product_id.name, 35)})
            qty = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'QTY'})
            qty.put({'BOTSID': 'QTY',
                     'C186.6063': '12',
                     'C186.6060': int(move.product_uom_qty)})
            qty = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'QTY'})
            qty.put({'BOTSID': 'QTY',
                     'C186.6063': '59',
                     'C186.6060': int(move.product_uom_qty)})
            rff = lin.putloop({'BOTSID': 'LIN'}, {'BOTSID': 'RFF'})
            rff.put({'BOTSID': 'RFF',
                     'C506.1153': 'ON',
                     'C506.1154': picking.origin and
                     self.limit_string(picking.origin, 35) or ''})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'CNT',
                'C270.6069': '1',
                'C270.6066': int(total_qty)})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'CNT',
                'C270.6069': '2',
                'C270.6066': int(count) - 1})
        out.put({
            'BOTSID': 'UNH'}, {
                'BOTSID': 'UNT',
                '0074': out.getcount() + 1,
                '0062': self.get_picking_name(picking.name)})
        out.writeall()
        return out.record2string(out.lex_records)

    @api.multi
    def compose_edi_picking(self, picking):
        configdir = 'config'
        botsinit.generalinit(configdir)
        process_name = 'odoo_get_edi'
        botsglobal.logger = botsinit.initenginelogging(process_name)
        una, header, footer = self.get_edi_picking_envelops(picking)
        body = self.get_edi_picking_body(picking)
        content = ''.join([una, header, body, footer])
        return content

    @api.multi
    def process_picking_out_files(self, pickings):
        edi_doc = False
        for picking in pickings:
            content = self.compose_edi_picking(picking)
            pick_name = self.get_picking_name(picking.name)
            edi_doc = self.create({
                'name': pick_name,
                'ttype': 'picking',
                'import_log': ''})
            try:
                file_path = self.write_out_file('pickings', '.'.join(
                    [pick_name, 'edi']), content)
            except IOError:
                edi_doc.import_log = '\n'.join([edi_doc.import_log, _(
                    'Cannot export: %s. File Structure Error: %s') % (
                        picking.name, _(
                            'See if out path is defined in Settings / '
                            'Companies / Companies > Configuration > EDI '
                            'Parameters > Out path. Inside this path, you must'
                            ' have a directory called \'pickings\'.'))])
                edi_doc.state = 'error'
                continue
            except Exception as e:
                edi_doc.import_log = '\n'.join([
                    edi_doc.import_log,
                    _('Cannot export: %s. Error: %s') %
                    (picking.name, str(e.args))])
                edi_doc.state = 'error'
                continue
            picking.edi_doc_id = edi_doc.id
            edi_doc.import_log = '\n'.join(
                [edi_doc.import_log, 'OK: %s' % picking.name])
            edi_doc.file_name = file_path
            edi_doc.picking_id = picking.id
            edi_doc.state = 'exported'
        return edi_doc

    @api.one
    def export_picking_again(self):
        return self.process_picking_out_files([self.picking_id])
