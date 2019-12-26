###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import base64
import io

import logging
_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class WizardProductSupplierinfoImport(models.TransientModel):
    _name = 'wizard.product.supplierinfo.import'
    _description = 'Wizard to import supplier pricelist'

    data_file = fields.Binary(
        string='Pricelist file',
        required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Supplier')
    state = fields.Selection(
        string='State',
        selection=[('step_1', 'Step 1'),
                   ('step_2', 'Step 2'),
                   ('step_done', 'Done')],
        required=True,
        default='step_1')
    supplierinfo_import_lines = fields.One2many(
        comodel_name='wizard.supplierinfo.import.line',
        inverse_name='wizard_id',
        string='Pricelists',
        readonly=True)
    product_import_lines = fields.One2many(
        comodel_name='wizard.product.import.line',
        inverse_name='wizard_id',
        string='Poducts',
        readonly=True)

    def _validate_row(self, row):
        num_values = [
            'price', 'list_price', 'garage_price', 'min_qty']
        for item in num_values:
            if not row[item] or pd.isnull(row[item]):
                row[item] = None
                continue
            try:
                float(row[item])
            except ValueError:
                raise UserError(
                    _('Value "%s" in row %s isn\'t a number') %
                    (row[item], item))
        return row

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

    def _manage_pricelist_item(self, pricelist_item, product_tmpl, row):
        if pricelist_item:
            pricelist_item.write({
                'compute_price': 'fixed',
                'fixed_price': row['garage_price'],
            })
            return pricelist_item
        return self.env['product.pricelist.item'].create({
            'pricelist_id': self.env.ref('product.list0').id,
            'product_tmpl_id': product_tmpl.id,
            'applied_on': '1_product',
            'compute_price': 'fixed',
            'fixed_price': row['garage_price'],
        })

    def _manage_stock_warehouse_orderpoint(self, product_tmpl, row):
        stock_rule = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', product_tmpl.product_variant_ids[0].id)
        ], limit=1)
        if stock_rule:
            stock_rule.product_min_qty = row['min_qty']
            return
        self.env['stock.warehouse.orderpoint'].create({
            'product_id': product_tmpl.product_variant_ids[0].id,
            'product_min_qty': row['min_qty'],
            'product_max_qty': 0,
        })

    def _create_product_line(self, action, row, product_tmpl):
        return self.env['wizard.product.import.line'].create({
            'wizard_id': self.id,
            'action': action,
            'default_code': row['default_code'],
            'name': (
                not pd.isnull(row['name']) and row['name'] or
                product_tmpl.name),
            'garage_price': row['garage_price'],
            'min_qty': row['min_qty'],
        })

    def _create_supplierinfo_line(self, action, currency, row, product_tmpl):
        return self.env['wizard.supplierinfo.import.line'].create({
            'wizard_id': self.id,
            'name': (
                not pd.isnull(row['name']) and
                row['name'] or product_tmpl.name),
            'action': action,
            'price': row['price'],
            'currency_id': currency and currency.id or None,
        })

    @api.multi
    def _get_file(self):
        fname = io.BytesIO()
        fname.write(base64.b64decode(self.data_file))
        return fname

    def _get_req_cols(self):
        return ['default_code']

    def _get_pricelist_vals(self):
        return ['price']

    def _get_product_vals(self):
        return ['default_code', 'list_price', 'name', 'list_price']

    @api.multi
    def action_to_step_2(self):
        self.ensure_one()
        fname = self._get_file()
        df = pd.read_excel(
            fname, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        req_cols = self._get_req_cols()
        cols_unknow = [c for c in req_cols if c not in df.columns]
        if cols_unknow:
            raise UserError(
                _('Columns "%s" not exists') % ', '.join(cols_unknow))
        for index, row in df.iterrows():
            row['default_code'] = str(row['default_code']).strip().upper()
            if row['name'] and not pd.isnull(row['name']):
                row['name'] = row['name'].strip()
            for item in req_cols:
                if pd.isnull(row[item]):
                    raise UserError(
                        _('Value of column %s in row %s is empty') %
                        (item, index + 1))
            row = self._validate_row(row)
            product_tmpls = self.env['product.template'].search([
                ('default_code', '=', row['default_code'])])
            if not product_tmpls:
                if not row['name'] or pd.isnull(row['name']):
                    raise UserError(
                        _('Product name is necessary for create "%s"') %
                        row['default_code'])
            if len(product_tmpls) > 1:
                raise UserError(
                    _('Product reference "%s" return more that one record') %
                    row['default_code'])
            if product_tmpls:
                action = 'update'
            else:
                action = 'create'
            self._create_product_line(action, row, product_tmpls)
            pricelists = self.env['product.supplierinfo'].search([
                ('name', '=', self.partner_id.id),
                ('product_tmpl_id', '=', product_tmpls.id),
            ])
            if len(pricelists) > 1:
                raise UserError(
                    _('There are more than one sale pricelist for ref "%s"') %
                    row['default_code'])
            action = pricelists and 'update' or 'create'
            currencies = self.env['res.currency'].search([
                ('name', '=', row['currency']),
            ])
            if len(currencies) > 1:
                raise UserError(
                    _('There are more than one currency for "%s"') %
                    row['currency'])
            if not currencies and not pd.isnull(row['currency']):
                raise UserError(
                    _('Currency with code "%s" not found') %
                    row['currency'])
            self._create_supplierinfo_line(
                action, currencies, row, product_tmpls)
        self.write({'state': 'step_2'})
        return self._reopen_view()

    @api.multi
    def action_to_step_done(self):
        self.ensure_one()
        pricelist_item = None
        fname = self._get_file()
        df = pd.read_excel(
            fname, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        for index, row in df.iterrows():
            row = self._validate_row(row)
            row['default_code'] = str(row['default_code']).strip().upper()
            if row['name'] and not pd.isnull(row['name']):
                row['name'] = row['name'].strip()
            product_tmpl = self.env['product.template'].search([
                ('default_code', '=', row['default_code']),
            ], limit=1)
            product_dict = {}
            for field in self._get_product_vals():
                if row[field] and not pd.isnull(row[field]):
                    product_dict[field] = row[field]
            if not product_tmpl:
                if 'name' not in product_dict:
                    raise UserError(
                        _('Product name is necessary for create "%s"') %
                        row['default_code'])
                product_dict['type'] = 'product'
                product_tmpl = self.env['product.template'].create(
                    product_dict)
            else:
                product_tmpl.write(product_dict)
                pricelist_item = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', self.env.ref('product.list0').id),
                    ('product_tmpl_id', '=', product_tmpl.id,),
                ])
            if row['min_qty'] and not pd.isnull(row['min_qty']):
                self._manage_stock_warehouse_orderpoint(product_tmpl, row)
            if row['garage_price'] and not pd.isnull(row['garage_price']):
                self._manage_pricelist_item(pricelist_item, product_tmpl, row)
            pricelist = self.env['product.supplierinfo'].search([
                ('name', '=', self.partner_id.id),
                ('product_tmpl_id', '=', product_tmpl.id),
            ], limit=1)
            pricelist_dict = {
                'name': self.partner_id.id,
                'product_tmpl_id': product_tmpl.id,
            }
            currency = self.env['res.currency'].search([
                ('name', '=', row['currency']),
            ], limit=1)
            if currency:
                pricelist_dict['currency_id'] = currency.id
            for field in self._get_pricelist_vals():
                if row[field] and not pd.isnull(row[field]):
                    pricelist_dict[field] = row[field]
            if pricelist:
                pricelist.write(pricelist_dict)
            else:
                self.env['product.supplierinfo'].create(pricelist_dict)
        self.write({'state': 'step_done'})
        return self._reopen_view()


class WizardSupplierInfoImportLine(models.TransientModel):
    _name = 'wizard.supplierinfo.import.line'
    _description = 'Wizard import supplier info line'

    wizard_id = fields.Many2one(
        comodel_name='wizard.product.supplierinfo.import',
        string='Wizard',
        ondelete='cascade',
        readonly=True,
        required=True)
    action = fields.Selection(
        string='Action',
        selection=[('update', 'update'),
                   ('create', 'create')],
        required=True)
    price = fields.Float(
        string='Price')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')
    name = fields.Char(
        string='Product name')


class WizardProductSupplierInfoImportLine(models.TransientModel):
    _name = 'wizard.product.import.line'
    _description = 'Wizard import product line'

    wizard_id = fields.Many2one(
        comodel_name='wizard.product.supplierinfo.import',
        string='Wizard',
        ondelete='cascade',
        readonly=True,
        required=True)
    action = fields.Selection(
        string='Action',
        selection=[('update', 'update'),
                   ('create', 'create')],
        required=True)
    default_code = fields.Char(
        string='Product reference')
    name = fields.Char(
        string='Product name')
    garage_price = fields.Float(
        string='Garage price')
    min_qty = fields.Float(
        string='Minimum quantity')
