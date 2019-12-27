# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import logging
import requests
import json
from tempfile import NamedTemporaryFile
from openerp import models, fields, api, exceptions, _

_log = logging.getLogger(__name__)


class QueryBookingMethabook(models.TransientModel):
    _name = 'query.booking.methabook'
    _description = 'Query Booking Methabook'

    state = fields.Selection(
        string='State',
        selection=[
            ('step_1', 'Step 1'),
            ('done', 'Done')
        ],
        default='step_1',
    )
    booking_locator = fields.Text(
        string='Locator',
        required=True,
        help='One or more locator separate by ,',
    )
    connection_log = fields.Text(
        string='Log',
    )
    booking_file = fields.Char(
        string='Booking File',
    )

    @api.multi
    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {}}

    @api.multi
    def button_query_booking(self):
        self.ensure_one()
        webservice_booking_check = self.env.ref(
            'booking_webservice_methabook.bw_methabook_query_booking')
        if not webservice_booking_check:
            raise exceptions.Warning(
                _('Not Webservice Methabook Query defined, abort'))
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Api-Key': webservice_booking_check.api_key}
        url = webservice_booking_check.url
        url += '?locators=%s' % self.booking_locator
        res = requests.get(url, headers=headers)
        if not res and not res.text:
            raise exceptions.Warning(_('No data return from webservice'))
        data = json.loads(res.text, encoding='utf-8')
        connection_log = json.dumps(data, indent=4, sort_keys=True)
        data['Export']['Customers'] = []
        data['Export']['Suppliers'] = []
        data['Export']['Zones'] = [],
        data['Export']['ExportId'] = 'Webservice manual',
        data['Export']['ExportedAt'] = 'Webservice manual',
        fileobj = NamedTemporaryFile('w+', suffix='.json', delete=False,)
        json.dump(data, fileobj, ensure_ascii=False)
        booking_file = fileobj.name
        fileobj.close()
        self.write({
            'state': 'done',
            'connection_log': connection_log,
            'booking_file': booking_file,
        })
        return self._reopen_view()

    @api.multi
    def button_send_file(self):
        self.ensure_one()
        if not self.booking_file:
            raise exceptions.Warning(_('Not booking file generate'))
        self.env['booking.webservice'].sudo().mt_first_load_bookings_json(
            mode='booking', booking_file=self.booking_file)
        return {'type': 'ir.actions.act_window_close'}
