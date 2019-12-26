# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import logging
_log = logging.getLogger(__name__)
try:
    from bots import inmessage, outmessage, botsinit, botsglobal
    from bots.outmessage import json as json_class
    from os import listdir, remove, rename
    from os.path import isfile, join, exists
    import atexit
except ImportError:
    _log.warning('bots python lib not installed.')


class EdifactDocument(models.Model):
    _name = 'edifact.document'
    _descripction = 'Edifact Document'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        track_visibility='onchange')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=(lambda self: self.env['res.company']._company_default_get(
            'edifact.document')))
    ttype = fields.Selection(
        selection=[
            ('order', 'Sale Order'),
            ('picking', 'Stock Picking'),
            ('invoice', 'Out Invoice'),
            ('voucher', 'Customer Voucher')
        ],
        string='Document Type',
        track_visibility='onchange')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('imported', 'Imported'),
            ('exported', 'Exported'),
            ('error', 'Error'),
        ],
        string='State',
        required=True,
        default='draft')
    date = fields.Datetime(
        string='Creation Date',
        required=True,
        default=fields.Datetime.now(),
        track_visibility='onchange')
    import_log = fields.Text(
        string='Import Log',
        translate=True)
    file_name = fields.Char(
        string='File Name')

    @api.multi
    def limit_string(self, string, num_char):
        return string and string[:num_char] or ''

    @api.multi
    def get_order_number(self, origin):
        order = self.env['sale.order'].search([(
            'name', '=', origin)])
        return order and self.limit_string(order[0].client_order_ref, 35) or (
            self.limit_string(origin, 35))

    @api.multi
    def get_picking(self, origin):
        if not origin:
            return ''
        order = self.env['sale.order'].search([(
            'name', '=', origin)])
        if not order:
            return origin
        return order.picking_ids and self.limit_string(
            order.picking_ids[0].name, 35) or (self.limit_string(origin, 35))

    @api.multi
    def ls_files(self, path, ttype=None):
        if ttype:
            path = '/'.join([path, ttype])
        if exists(path):
            return ['/'.join([path, arch])
                    for arch in listdir(path) if isfile(join(path, arch))]
        return []

    @api.multi
    def get_path(self, ttype):
        company_obj = self.env['res.company']
        company_id = company_obj._company_default_get('sale.order')
        company = company_obj.browse(company_id)
        if not company:
            return False
        if ttype == 'in':
            return company.in_path
        if ttype == 'out':
            return company.out_path
        if ttype == 'duplicated':
            return company.duplicated_path

    @api.multi
    def get_user(self):
        company_obj = self.env['res.company']
        company_id = company_obj._company_default_get('sale.order')
        company = company_obj.browse(company_id)
        return company and company.user_id or None

    @api.multi
    def delete_file(self, path):
        remove(path)

    @api.multi
    def move_file_to_duplicated(self, path):
        path_split = path.split('/')
        file_name = path_split[len(path_split) and len(path_split) - 1 or '']
        rename(path, '/'.join([self.get_path('duplicated'), file_name]))

    @api.multi
    def read_in_files(self, ttype=None):
        path = self.get_path('in')
        return self.ls_files(path, ttype)

    @api.multi
    def write_out_file(self, ttype, file_name, file_content):
        path = self.get_path('out')
        f = open('/'.join([path, ttype, file_name]), 'w+')
        f.write(file_content)
        f.close()
        return '/'.join([path, ttype, file_name])

    @api.multi
    def read_from_file(self, path):
        configdir = 'config'
        botsinit.generalinit(configdir)
        process_name = 'odoo_get_edi'
        botsglobal.logger = botsinit.initenginelogging(process_name)
        atexit.register(logging.shutdown)
        ta_info = {
            'alt': '',
            'charset': '',
            'command': 'new',
            'editype': 'edifact',
            'filename': path,
            'fromchannel': '',
            'frompartner': '',
            'idroute': '',
            'messagetype': 'edifact',
            'testindicator': '',
            'topartner': ''}
        try:
            edifile = inmessage.parse_edi_file(**ta_info)
        except Exception as e:
            if '[A59]' in str(e):
                raise exceptions.Warning(
                    _('Edi file has codification errors.'),
                    _('Check accents and other characters not allowed '
                      'in the edi document'))
            raise exceptions.Warning(_(
                'It has occurred following error: %s.' % e))
        json_ins = outmessage.json(edifile.ta_info)
        struc = [{ms.root.record['BOTSID']:
                 json_class._node2json(json_ins, ms.root)}
                 for ms in edifile.nextmessage()]
        return struc
