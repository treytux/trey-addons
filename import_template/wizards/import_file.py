# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

from openerp import _, api, exceptions, fields, models

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ImportFile(models.TransientModel):
    _name = 'import.file'
    _description = 'Wizard to import files with template'

    template_id = fields.Many2one(
        comodel_name='import.template',
        string='Template',
        required=True,
    )
    template_description = fields.Html(
        related='template_id.description',
        readonly=True,
    )
    file_filename = fields.Char(
        string='Filename',
    )
    file = fields.Binary(
        string='File',
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('select_template', 'Template selection'),
            ('simulation', 'Simulation'),
            ('step_done', 'Done'),
            ('orm_error', 'Errors'),
        ],
        required=True,
        default='select_template',
    )
    line_ids = fields.One2many(
        comodel_name='import.file.line',
        inverse_name='wizard_id',
        string='Lines',
        readonly=True,
    )
    total_warn = fields.Integer(
        string='Warnings',
        compute='_compute_totals',
    )
    total_error = fields.Integer(
        string='Errors',
        compute='_compute_totals',
    )
    total_rows = fields.Integer(
        string='Total rows',
        readonly=True,
    )
    simulate = fields.Boolean(
        string='Simulate before import',
        default=True,
        compute='_compute_simulate',
    )

    @api.one
    @api.depends('template_id')
    def _compute_simulate(self):
        for wizard in self:
            wizard.simulate = wizard.template_id.has_simulation

    @api.one
    @api.depends('line_ids')
    def _compute_totals(self):
        for wizard in self:
            wizard.total_warn = len(
                wizard.line_ids.filtered(lambda l: l.type == 'warn'))
            wizard.total_error = len(
                wizard.line_ids.filtered(lambda l: l.type == 'error'))

    @api.multi
    def action_open_template(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.template_id.id,
            'res_model': 'import.template',
            'context': {},
        }

    @api.multi
    def dataframe_get(self):
        self.ensure_one()
        buf = io.BytesIO()
        buf.write(base64.b64decode(self.file))
        buf.seek(0)
        ext = self.file_filename.split('.')[-1:][0]
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(
                buf, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        elif ext in ['csv']:
            # @TODO Crear campo sep para que lo introduzca el usuario. Por
            # defecto: ','
            df = pd.read_csv(
                buf, encoding='utf-8', na_values=['NULL'], sep=',')
            # df = df.fillna(False)
        elif ext in ['txt']:
            df = pd.read_csv(
                buf, encoding='utf-8', na_values=['NULL'], sep='\t')
        else:
            raise exceptions.Warning(_(
                'File extension must be \'xlsx\' or \'xlsx\' for Excel or '
                '\'csv\' for csv.'))
        return df.where((pd.notnull(df)), None)

    @api.multi
    def dataframe_required_columns(self, df, cols):
        missing_cols = [c for c in cols if c not in df]
        if missing_cols:
            raise exceptions.Warning(
                _('Missing columns in file: %s.') % ', '.join(missing_cols))
        return True

    @api.multi
    def _parse_with_cast(self, cast, value):
        try:
            return cast(str(value).strip())
        except Exception:
            return None

    @api.multi
    def _parse_integer(self, value, field):
        value = ''.join([v for v in str(value) if v in '0123456789+-'])
        return 0 if value == '' else self._parse_with_cast(int, value)

    @api.multi
    def _parse_float(self, value, field):
        value = ''.join([
            v for v in str(value).replace(',', '.') if v in '0123456789+-.'])
        return 0.0 if value == '' else self._parse_with_cast(float, value)

    @api.multi
    def _parse_bool(self, value, field):
        value = value and value.strip().lower() or ''
        false_vals = ['false', '0', 'no', '', 'null', 'none']
        return False if value in false_vals else True

    @api.multi
    def _parse_selection(self, value, field):
        value = value and value.strip().lower() or ''
        return value if value in field.get_values(self.env) else False

    @api.multi
    def _parse_char(self, value, field):
        if isinstance(value, float) and value % 1 == 0.0:
            value = str(int(value))
        return value or ''

    @api.multi
    def _parse_text(self, value, field):
        return value or ''

    @api.multi
    def parser(self, model, data):
        data_parsed = data.copy()
        model_obj = self.env[model]
        for field_name, val in data.items():
            if field_name not in model_obj._fields:
                _log.warning('Field %s unknow in model %s.' % (
                    field_name, model_obj._name))
                continue
            method_name = '_parse_%s' % model_obj._fields[field_name].type
            if hasattr(self, method_name):
                fnc = getattr(self, method_name)
                data_parsed[field_name] = fnc(
                    val, model_obj._fields[field_name])
                continue
            _log.warning('Field %s has not parser.' % field_name)
        errors = self._check_required_fields(model, data_parsed)
        return data_parsed, errors

    @api.multi
    def _check_required_fields(self, model, data):
        required = [
            n for n, f in self.env[model]._fields.items() if f.required]
        missings = []
        for k, v in data.items():
            if k in required:
                if self.env[model]._fields[k].type in ('int', 'float'):
                    if k in (0, 0.0):
                        missings.append(k)
                else:
                    if v in (None, False, ''):
                        missings.append(k)
        msg = _(
            'The \'%s\' field is required, you must fill it with a '
            'valid value.')
        return [msg % m for m in missings]

    @api.multi
    def get_data_row(self, wizard_tmpl_model, model, df, row):
        data = {}
        no_fields = []
        no_function = []
        all_errors = []
        relational_types = ('many2one', 'many2many', 'one2many')
        for c in df.columns:
            if c in self.env[model]._fields.keys():
                if self.env[model]._fields[c].type not in relational_types:
                    data[c] = row[c]
                    continue
                method_name = '%s_get_or_create' % c
                if hasattr(wizard_tmpl_model, method_name):
                    fnc = getattr(wizard_tmpl_model, method_name)
                    id, errors = fnc(row[c])
                    for error in errors:
                        all_errors.append(error)
                    data[c] = id
                else:
                    no_function.append(c)
            elif ':' in c:
                continue
            else:
                no_fields.append(c)
        msg = _('The \'%s\' column is not a field for model.')
        for n in no_fields:
            all_errors.append(msg % n)
        msg = _(
            'The \'%s\' column is a relational field and there is no defined '
            'function to convert it.')
        for n in no_function:
            all_errors.append(msg % n)
        return data, all_errors

    @api.multi
    def savepoint(self, name):
        self._cr.execute('SAVEPOINT %s' % name)

    @api.multi
    def rollback(self, name):
        self._cr.execute('ROLLBACK TO SAVEPOINT %s' % name)
        self.pool.clear_caches()

    @api.multi
    def release(self, name):
        self._cr.execute('RELEASE SAVEPOINT %s' % name)

    @api.multi
    def open_template_form(self):
        if not self.file:
            raise exceptions.Warning(_('You must choose a file to import!'))
        return self.template_id.action_open_form(self)

    @api.multi
    def action_import_from_simulation(self):
        return self.template_id.action_open_from_simulation_form(self)

    @api.multi
    def open_done(self):
        self.state = 'done'

    @api.multi
    def step(self, index, msg=''):
        _log.info('[%s/%s] %s' % (index, self.total_rows, msg))

    @api.multi
    def error(self, index, msg=''):
        self.line_ids.create({
            'wizard_id': self.id,
            'type': 'error',
            'name': '%s: %s' % (index, msg),
        })

    @api.multi
    def warn(self, index, msg=''):
        self.line_ids.create({
            'wizard_id': self.id,
            'type': 'warn',
            'name': '%s: %s' % (index, msg),
        })


class ImportFileLine(models.TransientModel):
    _name = 'import.file.line'
    _description = 'Lines of wizard import files with template'

    name = fields.Char(
        string='Message',
    )
    wizard_id = fields.Many2one(
        comodel_name='import.file',
        string='Wizard',
    )
    type = fields.Selection(
        selection=[
            ('warn', 'Warning'),
            ('error', 'Error'),
        ],
        string='Type',
        default='warn',
    )
