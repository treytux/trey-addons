# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import _, api, exceptions, fields, models, tools
from dateutil.relativedelta import relativedelta
from pytz import timezone
from datetime import datetime
import base64
import io
import logging
import os

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ImportProductPricelistIncrease(models.TransientModel):
    _name = 'import.product.pricelist.increase'
    _description = 'Import pricelist increase file'

    pricelist_type = fields.Selection(
        selection=[
            ('purchase', 'Purchase'),
        ],
        string='Pricelist type',
        default='purchase',
        required=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
    )
    template_file = fields.Binary(
        string='Template file',
        attachment=True,
        readonly=True,
    )
    template_filename = fields.Char(
        string='Template file name',
        readonly=True,
    )
    file = fields.Binary(
        string='File',
        filters='*.xls, *.xlsx',
        required=True,
        help='If the "Increase (%)" column of the file has a positive value, '
             'it will be imported as an increment. If on the contrary it is '
             'negative, it will be imported as a discount.'
    )
    file_filename = fields.Char(
        string='File name',
    )
    base = fields.Selection(
        selection=[
            ('public_price', 'Public price'),
            ('cost_price', 'Cost price'),
            ('supplierinfo_price', 'Supplier prices on the product form'),
        ],
        string='Item based on',
        default='supplierinfo_price',
        required=True,
        help='Base price for computation.',
    )
    line_ids = fields.One2many(
        comodel_name='import.product.pricelist.increase.line',
        inverse_name='wizard_id',
        string='Lines',
        readonly=True,
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('import_file', 'Import file'),
            ('simulation', 'Simulation'),
            ('step_done', 'Done'),
        ],
        required=True,
        default='import_file',
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

    @api.model
    def default_get(self, fields):
        res = super(ImportProductPricelistIncrease, self).default_get(fields)
        module_path = os.path.dirname(os.path.dirname(__file__))
        tmpl_file_name = 'sample_template.xls'
        template_file_path = os.path.join(
            module_path, 'data/%s' % tmpl_file_name)
        res.update({
            'template_file': base64.b64encode(
                open(template_file_path, 'rb').read()),
            'template_filename': tmpl_file_name,
        })
        return res

    def get_mapped_base_pricelist(self, base):
        if base == 'public_price':
            return 1
        elif base == 'cost_price':
            return 2
        elif base == 'supplierinfo_price':
            return -2
        else:
            raise exceptions.Warning(_('\'%s\' option not allowed!'))

    def convert_date_to_tz(self, date, time_zone):
        tz_utc = timezone('UTC')
        tz_user = timezone(time_zone)
        local_date_now = tz_utc.localize(date)
        date_now = local_date_now.astimezone(tz_user)
        return datetime.strftime(
            date_now,
            tools.DEFAULT_SERVER_DATETIME_FORMAT
        )

    @api.multi
    def error(self, index, msg=''):
        self.line_ids.create({
            'wizard_id': self.id,
            'ttype': 'error',
            'name': '%s: %s' % (index, msg),
        })

    @api.multi
    def warn(self, index, msg=''):
        self.line_ids.create({
            'wizard_id': self.id,
            'ttype': 'warn',
            'name': '%s: %s' % (index, msg),
        })

    @api.one
    @api.depends('line_ids')
    def _compute_totals(self):
        for wizard in self:
            wizard.total_warn = len(
                wizard.line_ids.filtered(lambda l: l.ttype == 'warn'))
            wizard.total_error = len(
                wizard.line_ids.filtered(lambda l: l.ttype == 'error'))

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

    def save_errors(self, errors):
        for error in errors:
            if error:
                self.error(error[0], error[1])

    @api.multi
    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def get_data_version(self, pricelist):
        data_update_first_version = {}
        errors = []
        try:
            version_obj = self.env['product.pricelist.version']
            first_version = version_obj.search([
                ('pricelist_id', '=', pricelist.id),
            ], order='date_start', limit=1)
            today = fields.Datetime.from_string(fields.Date.today())
            if not first_version:
                date_start = today - relativedelta(years=1)
                date_end = (
                    today - relativedelta(years=1) + relativedelta(days=1))
            else:
                if not first_version.date_start and not first_version.date_end:
                    date_start = today - relativedelta(years=1)
                    date_end = (
                        today - relativedelta(years=1) + relativedelta(days=1))
                    data_update_first_version = {
                        first_version: {
                            'date_start': (
                                today - relativedelta(years=1) +
                                relativedelta(days=2)),
                        }
                    }
                elif first_version.date_start:
                    date_start = (
                        fields.Datetime.from_string(first_version.date_start) -
                        relativedelta(years=1))
                    date_end = (
                        fields.Datetime.from_string(first_version.date_start) -
                        relativedelta(years=1) + relativedelta(days=1))
                elif first_version.date_end:
                    date_start = (
                        fields.Datetime.from_string(first_version.date_end) -
                        relativedelta(years=2))
                    date_end = (
                        fields.Datetime.from_string(first_version.date_end) -
                        relativedelta(years=2) + relativedelta(days=1))
                    data_update_first_version = {
                        first_version: {
                            'date_start': (
                                fields.Datetime.from_string(
                                    first_version.date_end) -
                                relativedelta(years=1)),
                        }
                    }
            date_now = self.convert_date_to_tz(
                datetime.now(), self.env.user.tz or 'UTC')
            data_import_version = {
                'pricelist_id': pricelist.id,
                'name': _('Version imported %s') % date_now,
                'date_start': date_start,
                'date_end': date_end,
                'items_id': [(0, 0, {
                    'name': _('Generic for all products'),
                    'sequence': 10,
                    'base': self.get_mapped_base_pricelist(self.base),
                })],
            }
        except Exception as e:
            errors.append(('', _(e)))
        return data_import_version, data_update_first_version, errors

    def get_data_item(self, data_import_version, datas):
        data_item = {}
        errors = []
        default_code = datas[0]
        increase_percent = datas[1]
        products = self.env['product.product'].search([
            ('default_code', '=', default_code),
        ])
        if len(products) < 1:
            errors.append(
                ('', _(
                    'No product was found with the default code \'%s\'.') % (
                    default_code)))
        elif len(products) > 1:
            errors.append(
                ('', _('There are more than one product with the default code '
                       '\'%s\'.') % default_code))
        else:
            data_item = {
                'name': _('Product %s') % default_code,
                'product_id': products[0].id,
                'sequence': 5,
                'base': self.get_mapped_base_pricelist(self.base),
                'price_discount': float(increase_percent) / 100,
            }
        return data_item, errors

    @api.multi
    def action_import_simulation(self):
        self.action_import(simulation=True)
        self.state = 'simulation'
        return self._reopen_view()

    @api.multi
    def action_import_real(self):
        self.action_import(simulation=False)
        self.state = 'step_done'
        return self._reopen_view()

    @api.multi
    def action_import(self, simulation=True):
        def _is_float(value):
            try:
                return float(value)
            except Exception:
                return False
        all_errors = []
        self.line_ids.unlink()
        self.savepoint('import_template_supplierinfo')
        try:
            fname = io.BytesIO()
            fname.write(base64.b64decode(self.file))
            df = pd.read_excel(
                fname, engine='xlrd', encoding='utf-8', na_values=['NULL'],
                converters={'Increase (%)': float})
            df = df.where((pd.notnull(df)), None)
            self.total_rows = len(df)
            header = [col.lower() for col in df.columns]
            if _('Default code').upper() not in header[0].upper():
                all_errors.append(
                    ('', _(
                        'The first column must be called \'Default code\'!')))
            if _('Increase (%)').upper() not in header[1].upper():
                all_errors.append(
                    ('', _(
                        'The second column must be called \'Increase (%)\'!')))
            if len(df) == 0:
                all_errors.append(
                    ('', _('The file does not contain data.')))
            data_import_version, data_update_first_version, errors = (
                self.get_data_version(self.pricelist_id))
            for error in errors:
                all_errors.append(error)
            data_items = []
            for index, row in df.iterrows():
                default_code = row[0]
                increase_percent = row[1]
                if not default_code:
                    all_errors.append(
                        (index, _('\'Default code\' field cannot be empty.')))
                    continue
                if not increase_percent:
                    all_errors.append(
                        (index, _('\'Increase (%)\' field cannot be empty.')))
                    continue
                if not _is_float(increase_percent):
                    all_errors.append(
                        (index, _('\'Increase (%)\' field must be an float.')))
                    continue
                data_item, errors = self.get_data_item(
                    data_import_version, [default_code, increase_percent])
                for error in errors:
                    all_errors.append(error)
                data_items.append(data_item)
            if simulation:
                self.rollback('import_template_supplierinfo')
                self.save_errors(all_errors)
                return
            self.save_errors(all_errors)
            row_error = self.line_ids.filtered(lambda ln: ln.ttype == 'error')
            if row_error:
                self.rollback('import_template_supplierinfo')
                return
            if data_update_first_version:
                first_version = data_update_first_version.keys()[0]
                first_version.write(data_update_first_version[first_version])
            new_version = self.env['product.pricelist.version'].create(
                data_import_version)
            for data_item in data_items:
                data_item.update({
                    'price_version_id': new_version.id,
                })
                self.env['product.pricelist.item'].create(data_item)
            self.release('import_template_supplierinfo')
        except Exception as e:
            self.error('', e)
            self.rollback('import_template_supplierinfo')
        return []


class ImportProductPricelistIncreaseLine(models.TransientModel):
    _name = 'import.product.pricelist.increase.line'
    _description = 'Lines of wizard import pricelist increase file'

    name = fields.Char(
        string='Message',
    )
    wizard_id = fields.Many2one(
        comodel_name='import.product.pricelist.increase',
        string='Wizard',
    )
    ttype = fields.Selection(
        selection=[
            ('warn', 'Warning'),
            ('error', 'Error'),
        ],
        string='Type',
        default='warn',
    )
