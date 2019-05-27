# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
from datetime import datetime
import base64
import StringIO
import logging
_log = logging.getLogger(__name__)


class WizardManualImportBooking(models.TransientModel):
    _name = 'wizard.manual.import.booking'

    @api.multi
    def _get_file_name(self):
        self.file_name = _(
            'bookings_%s.xml') % datetime.datetime.now().strftime('%y%m%d%H%M')

    name = fields.Char(
        string='name')
    ffile = fields.Binary(
        string='File xml',
        filters='*.xml',
        required=True)
    file_name = fields.Char(
        string='File name',
        compute=_get_file_name)

    @api.one
    def button_ok(self):
        active_id = self.env.context.get('active_id', False)
        if not active_id:
            return
        webservice_id = self.env['booking.webservice'].browse(active_id)
        if not webservice_id.type == 'juniper':
            return
        if self.ffile:
            try:
                ffile = base64.decodestring(self.ffile)
                ffile = StringIO.StringIO(ffile)
            except Exception as e:
                raise exceptions.Warning(_(
                    'It has occurred following error: %s.' % e))
        file_xml = ffile.read()
        webservice_id.with_context(cron=False).update_bookings(file_xml)
