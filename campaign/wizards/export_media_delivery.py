# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _
import csv
import StringIO
import base64
import logging
_log = logging.getLogger(__name__)


class WizExportMediaDelivery(models.TransientModel):
    _name = 'wiz.export.media.delivery'
    _description = 'Wizard to export media delivery'

    @api.multi
    def _get_file_name(self):
        self.file_name = _('Media_delivery_%s.csv') % fields.Datetime.now()

    name = fields.Char(
        string='Empty')
    ffile = fields.Binary(
        string='File',
        filter='*.csv')
    file_name = fields.Char(
        string='File name',
        compute=_get_file_name)

    def get_address(self, trade):
        if not trade.exists():
            return ''
        addr = ''
        addr += trade.street and '%s\n' % trade.street or ''
        addr += trade.zip and '%s ' % trade.zip or ''
        addr += trade.city and '%s ' % trade.city or ''
        addr += trade.state_id and '(%s)' % trade.state_id.name or ''
        addr += trade.country_id and '(%s)' % trade.country_id.name or ''
        return addr

    @api.multi
    def button_accept(self):
        active_ids = self.env.context.get('active_ids', [])
        ofile = StringIO.StringIO()
        line_count = 0
        lines = []
        for delivery in self.env['media.delivery'].browse(active_ids):
            line_count += 1
            if line_count == 1:
                lines.append({
                    'media_line_id': 'Line ID',
                    'campaign': 'Campaign',
                    'trade_id': 'Trade ID',
                    'trade': 'Trade',
                    'trade_address': 'Trade address',
                    'trade_phone': 'Trade phone',
                    'trade_mobile': 'Trade mobile',
                    'trade_email': 'Trade email',
                    'activity': 'Activity',
                    'name_surveyed': 'Name surveyed',
                    'function_surveyed': 'Function surveyed',
                    'opening_days': 'Opening days',
                    'comment': 'Comment',
                    'media_type': 'Media type',
                    'requested': 'Requested',
                    'delivered': 'Delivered'})
            for mline in delivery.media_lines:
                if delivery.campaign_id.horeca:
                    lines.append({
                        'media_line_id': mline.id,
                        'campaign': mline.delivery_id.campaign_id.name,
                        'trade_id': (
                            mline.delivery_id.trade_id and
                            mline.delivery_id.trade_id.id or ''),
                        'trade': (mline.delivery_id.trade_id and
                                  mline.delivery_id.trade_id.name or None),
                        'trade_address': self.get_address(
                            mline.delivery_id.trade_id),
                        'trade_phone': mline.delivery_id.trade_id.phone,
                        'trade_mobile': mline.delivery_id.trade_id.mobile,
                        'trade_email': mline.delivery_id.trade_id.email,
                        'activity': mline.delivery_id.trade_id.activity,
                        'name_surveyed':
                            mline.delivery_id.trade_id.name_surveyed,
                        'function_surveyed':
                            mline.delivery_id.trade_id.function_surveyed,
                        'opening_days':
                            mline.delivery_id.trade_id.opening_days,
                        'comment': mline.delivery_id.trade_id.comment,
                        'media_type': mline.media_type,
                        'requested': mline.requested,
                        'delivered': mline.delivered})
                else:
                    lines.append({
                        'media_line_id': mline.id,
                        'campaign': mline.delivery_id.campaign_id.name,
                        'trade_id': (
                            mline.delivery_id.trade_id and
                            mline.delivery_id.trade_id.id or ''),
                        'trade': (mline.delivery_id.trade_id and
                                  mline.delivery_id.trade_id.name or None),
                        'trade_address': self.get_address(
                            mline.delivery_id.trade_id),
                        'trade_phone': '',
                        'trade_mobile': '',
                        'trade_email': '',
                        'activity': '',
                        'name_surveyed': '',
                        'function_surveyed': '',
                        'opening_days': '',
                        'comment': '',
                        'media_type': mline.media_type,
                        'requested': mline.requested,
                        'delivered': mline.delivered})
        a = csv.writer(ofile, delimiter=';', quotechar='"',
                       quoting=csv.QUOTE_ALL)
        for d in lines:
            trade = ''
            trade_address = ''
            if d['trade'] is not None:
                trade = d['trade'].encode('utf-8')
            if d['trade_address'] is not None:
                trade_address = d['trade_address'].encode('utf-8')
            a.writerow((
                d['media_line_id'], d['campaign'].encode('utf-8'),
                d['trade_id'], trade, trade_address,
                d['trade_phone'].encode('utf-8'),
                d['trade_mobile'].encode('utf-8'),
                d['trade_email'].encode('utf-8'),
                d['activity'].encode('utf-8'),
                d['name_surveyed'].encode('utf-8'),
                d['function_surveyed'].encode('utf-8'),
                d['opening_days'].encode('utf-8'),
                d['comment'].encode('utf-8'),
                d['media_type'].encode('utf-8'),
                d['requested'], d['delivered']))
        content = ofile.getvalue()
        content = base64.encodestring(content)

        self.write({'ffile': content})
        res = self.env['ir.model.data'].get_object_reference(
            'campaign', 'wizard_wiz_export_media_delivery_ok')
        res_id = res and res[1] or False
        return {
            'name': _('Export media delivery'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.export.media.delivery',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
