# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class MethabookLog(models.Model):
    _name = 'methabook.log'
    _order = 'date_import desc'

    name = fields.Char(
        string='Empty')
    model_name = fields.Char(
        string='Model name',
        readonly=True)
    methabook_id = fields.Integer(
        string='Methabook ID',
        readonly=True)
    date_import = fields.Datetime(
        string='Date import',
        default=fields.Datetime.now,
        readonly=True)
    ttype = fields.Selection(
        selection=[
            ('customer', 'Customer'),
            ('supplier', 'Supplier'),
            ('zone', 'Zone'),
            ('booking', 'Booking')],
        string='Type',
        readonly=True)
    import_data = fields.Text(
        string='Import data',
        readonly=True)
    log = fields.Text(
        string='Log',
        readonly=True)
    state = fields.Selection(
        selection=[
            ('bookings', 'Bookings'),
            ('error', 'Error'),
            ('info', 'Info')],
        string='State',
        default='error',
        required=True)

    @api.multi
    def add_log(self, model_name, methabook_id, ttype, import_data, log,
                state='error'):
        try:
            if methabook_id and not methabook_id.isdigit():
                methabook_id = -1
            return self.create({
                'model_name': model_name,
                'methabook_id': methabook_id,
                'ttype': ttype,
                'import_data': import_data,
                'log': log,
                'state': state})
        except Exception as e:
            import logging
            _log = logging.getLogger(__name__)
            _log.error(
                'Cant add a new log: Model: %s // methabook_id: %s // '
                'Ttype: %s // State: %s // Import_data: %s // Log: %s // '
                'Error: %s' %
                (model_name, methabook_id, ttype, state, import_data, log, e))
