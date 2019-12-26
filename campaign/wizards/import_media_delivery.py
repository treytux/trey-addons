# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import base64
import csv
import StringIO
# from tempfile import NamedTemporaryFile
import logging
_log = logging.getLogger(__name__)


class WizImportMediaDelivery(models.TransientModel):
    _name = 'wiz.import.media.delivery'
    _description = 'Wizard to import media delivery'

    name = fields.Char(
        string='Empty')
    ffile = fields.Binary(
        string='File csv',
        filters='*.csv',
        required=True)
    log_simulation = fields.Text(
        string='Log simulation error',
        readonly=True)
    log_write = fields.Text(
        string='Log write error',
        readonly=True)
    state = fields.Selection(
        string='State',
        selection=[
            ('draft', 'Draft'),
            ('simulation', 'Simulation'),
            ('done', 'Done')],
        required=True,
        default='draft')
    simulation = fields.Text(
        string='Simulation import',
        readonly=True)

    @api.multi
    def write_file_lines(self, data, header, operation):
        if operation == 'simule':
            selected_values = []
            selected_headers = []
            try:
                selected_headers.append(header[1])
                selected_headers.append(header[2])
                selected_headers.append(header[3])
                selected_headers.append(header[13])
                selected_headers.append(header[14])
                selected_headers.append(header[15])
                lines = ''
                for row in data:
                    lines += '''<tr>'''
                    selected_values.append(row[1])
                    selected_values.append(row[2])
                    selected_values.append(row[3])
                    selected_values.append(row[13])
                    selected_values.append(row[14])
                    selected_values.append(row[15])
                    for value in selected_values:
                        lines += '''<td>%s</td>''' % (value)
                    lines += '''</tr>'''
                    selected_values = []
                self.simulation = '''
                    <table class="table table-striped table-condensed">
                        <thead>
                            <tr>
                                <th>%s</th>
                            </tr>
                        </thead>
                        <tbody>
                            %s
                        </tbody>
                    </table>
                ''' % (('</th><th>').join(selected_headers), lines)
            except Exception as e:
                self.write({'log_simulation': e.message})
        if operation == 'write':
            try:
                line_id = header.index('line id')
                delivered = header.index('delivered')
                for lin in data:
                    delivery_line = self.env['media.delivery.lines'].browse(
                        int(lin[line_id]))
                    delivery_line.write({'delivered': lin[delivered]})
                    delivery_line.delivery_id.write({
                        'date_delivery': fields.Date.today(),
                        'state': 'pending_review'})
            except Exception as e:
                self.write({'log_write': e.message})
        return True

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
    def read_file(self):
        if self.ffile:
            # ***************************************************************
            # Save file in temporal folder for backup an sniffer csv format
            # ***************************************************************
            # file_obj = NamedTemporaryFile(
            #     'w+', suffix='.csv', delete=False)
            # file_obj.write(base64.decodestring(self.ffile))
            # path = file_obj.name
            # file_obj.close()

            ffile = base64.decodestring(self.ffile)
            ffile = StringIO.StringIO(ffile)
            reader = csv.reader(
                ffile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            # Open file
            # csvfile = open(path, "rb")
            # csvfile.seek(0)
            # # Reads file lines and creates wizard lines
            # reader = csv.reader(
            #     csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            # Reads file lines and creates wizard lines
            header = reader.next()
            # Change columns to lowercase
            header = [x.lower() for x in header]
            data = [row for row in reader]
            # csvfile.close()

            def is_int(value):
                try:
                    return int(value) >= 0
                except:
                    return False

            for row in data:
                if not is_int(row[0]):
                    raise exceptions.Warning(_(
                        'Column value must be an integer.'))
                if not is_int(row[15]):
                    raise exceptions.Warning(_(
                        'Column value must be an integer.'))
            return data, header
        return False

    @api.multi
    def button_simulation(self):
        data, header = self.read_file()
        self.write_file_lines(data, header, 'simule')
        self.state = 'simulation'
        return self._reopen_view()

    @api.multi
    def button_done(self):
        """Imports the file and creates the lines of the wizard."""
        self.ensure_one()
        if self.ffile:
            data, header = self.read_file()
            self.write_file_lines(data, header, 'write')
        self.state = 'done'
        return self._reopen_view()
