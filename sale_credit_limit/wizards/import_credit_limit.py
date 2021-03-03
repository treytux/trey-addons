# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import base64
import io
import re
import logging
_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ImportCreditLimit(models.TransientModel):
    _name = 'import.credit_limit'

    name = fields.Char(
        string='Empty',
    )
    ffile = fields.Binary(
        string='File',
        required=True,
        filters='*.xls, *.xlsx',
    )
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

    def clean_vat(self, vat):
        return re.sub('[^0-9a-zA-Z]+', '', vat)

    def get_partner(self, vat, partner_name=''):
        partner = ''
        error = ''
        vat = self.clean_vat(vat)
        partners = self.env['res.partner'].search([
            ('parent_id', '=', None),
            '|',
            ('vat', '=', vat),
            ('vat', '=', 'ES%s' % vat),
        ])
        if not partners:
            error = _('\nNo partner was found with the vat \'%s\'.') % vat
        elif len(partners) > 1:
            if not partner_name:
                error = _(
                    '\nThere is more than one partner with the vat \'%s\', '
                    'check it.') % vat
            else:
                partners = partners.filtered(lambda p: p.name == partner_name)
                if not partners:
                    error = _(
                        '\nThere is more than one partner that has the vat '
                        '\'%s\' assigned. We searched by name but no partner '
                        'was found with vat \'%s\' and name \'%s\'.') % (
                            vat, vat, partner_name)
                elif len(partners) > 1:
                    error = _(
                        '\nThere is more than one partner with the vat \'%s\' '
                        'and name \'%s\', check it.') % (vat, partner_name)
                else:
                    partner = partners[0]
        else:
            partner = partners[0]
        return partner, error

    @api.multi
    def write_file_lines(self, data, header, operation):
        if operation == 'simule':
            selected_values = []
            selected_headers = []
            log_simulation = ''
            try:
                selected_headers.append(header[0])
                selected_headers.append(header[1])
                if len(header) > 2:
                    selected_headers.append(header[2])
                selected_headers.append(_('PARTNER'))
                selected_headers.append(_('CHANGE TO DO'))
                lines = ''
                for row in data:
                    lines += '''<tr>'''
                    selected_values.append(row[0])
                    selected_values.append(row[1])
                    if len(header) > 2:
                        selected_values.append(row[2])
                    partner, error = self.get_partner(
                        row[0], len(row) > 2 and row[2] or '')
                    selected_values.append(
                        partner and partner.name or _('Not found.'))
                    if partner:
                        selected_values.append(_(
                            '\nCredit limit will be updated for partner %s: '
                            '%s => %s.') % (
                                partner.name, partner.credit_limit, row[1]))
                    if error:
                        selected_values.append(error)
                        log_simulation += error
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
                self.write({'log_simulation': log_simulation})
            except Exception as e:
                self.write({'log_simulation': e.message})
        if operation == 'write':
            try:
                log_write = ''
                for row in data:
                    partner, error = self.get_partner(
                        row[0], len(row) > 2 and row[2] or '')
                    if partner:
                        log_write += _(
                            '\nCredit limit updated for partner %s with vat '
                            '%s: %s => %s.') % (
                                partner.name, row[0], partner.credit_limit,
                                row[1])
                        partner.write({'credit_limit': row[1]})
                    else:
                        log_write += error
                self.write({'log_write': log_write})
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
        def _is_float(value):
            try:
                return float(value)
            except Exception:
                return False

        if self.ffile:
            fname = io.BytesIO()
            fname.write(base64.b64decode(self.ffile))
            df = pd.read_excel(
                fname, engine='xlrd', encoding='utf-8', na_values=['NULL'])
            df = df.where((pd.notnull(df)), None)
            header = [col.lower() for col in df.columns]
            if _('vat').upper() not in header[0].upper():
                raise exceptions.Warning(_(
                    'The first column must be called \'vat\'!'))
            if _('credit_limit').upper() not in header[1].upper():
                raise exceptions.Warning(_(
                    'The second column must be called \'credit_limit\'!'))
            data = []
            for index, row in df.iterrows():
                vat = row[0]
                credit = row[1]
                if not vat:
                    raise exceptions.Warning(_(
                        '\'vat\' field cannot be empty.'))
                if not _is_float(credit):
                    raise exceptions.Warning(_(
                        '\'credit_limit\' field must be an float.'))
                if len(row) > 2:
                    partner_name = row[2]
                    rows2add = (vat, credit, partner_name)
                else:
                    rows2add = (vat, credit)
                data.append(rows2add)
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
        self.ensure_one()
        data, header = self.read_file()
        self.write_file_lines(data, header, 'write')
        self.state = 'done'
        return self._reopen_view()
