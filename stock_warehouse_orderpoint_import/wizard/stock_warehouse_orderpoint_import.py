###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import base64
import io

import logging
_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class WizardStockWarehouseOrderpointImport(models.TransientModel):
    _name = 'wizard.stock.warehouse.orderpoint.import'
    _description = 'Wizard to import stock rules'

    data_file = fields.Binary(
        string='Pricelist file',
        required=True,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        domain=[('usage', '!=', 'view')],
        required=True,
        string='Location',
    )
    state = fields.Selection(
        string='State',
        selection=[('step_1', 'Step 1'),
                   ('step_done', 'Done')],
        required=True,
        default='step_1',
    )

    rows_imported = fields.Integer(
        default=0,
        string='Rows imported',
    )

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

    @api.multi
    def _get_file(self):
        fname = io.BytesIO()
        fname.write(base64.b64decode(self.data_file))
        return fname

    def _get_req_cols(self):
        return ['default_code']

    def _validate_row(self, row):
        num_values = ['product_min_qty', 'product_max_qty']
        if 'product_max_qty' in row:
            num_values += ['product_max_qty']
        for item in num_values:
            if pd.isnull(row[item]):
                row[item] = None
                continue
            try:
                float(row[item])
            except ValueError:
                raise UserError(
                    _('Value "%s" in row %s isn\'t a number') %
                    (row[item], item))
        return row

    def _get_update_fields(self):
        return ['product_min_qty', 'product_max_qty']

    def manage_reordering_rule(self, row, reordering_rule):
        rule_dict = {}
        if reordering_rule:
            for field in self._get_update_fields():
                if field in row and row[field] is not None:
                    rule_dict[field] = row[field]
            reordering_rule.write(rule_dict)
        else:
            for field in self._get_update_fields():
                if field not in row or row[field] is None:
                    rule_dict[field] = 0
                else:
                    rule_dict[field] = row[field]
            rule_dict.update({
                'location_id': self.location_id.id,
                'product_id': row['product_id'].id,
                'warehouse_id': row['stock_warehouse_id'].id,
            })
            self.env['stock.warehouse.orderpoint'].create(rule_dict)

    @api.multi
    def action_import(self):
        self.ensure_one()
        fname = self._get_file()
        df = pd.read_excel(
            fname, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        df = df.where((pd.notnull(df)), None)
        req_cols = self._get_req_cols()
        cols_unknow = [c for c in req_cols if c not in df.columns]
        if cols_unknow:
            raise UserError(
                _('Columns "%s" not exists') % ', '.join(cols_unknow))
        for index, row in df.iterrows():
            row['default_code'] = str(row['default_code']).strip().upper()
            for item in req_cols:
                if pd.isnull(row[item]):
                    raise UserError(
                        _('Value of column %s in row %s is empty') %
                        (item, index + 2))
            row = self._validate_row(row).to_dict()
            if isinstance(row['default_code'], float):
                row['default_code'] = str(int(row['default_code']))
            products = self.env['product.product'].search([
                ('default_code', '=', row['default_code'])])
            if not products:
                raise UserError(
                    _('Product "%s" not found') % row['default_code'])
            if len(products) > 1:
                raise UserError(
                    _('Product reference "%s" return more that one record') %
                    row['default_code'])
            row['product_id'] = products
            row['stock_warehouse_id'] = self.location_id.get_warehouse()
            reordering_rule = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', row['product_id'].id),
                ('warehouse_id', '=', row['stock_warehouse_id'].id),
            ], limit=1)
            self.manage_reordering_rule(row, reordering_rule)
        try:
            self.rows_imported = index + 1
        except Exception:
            raise ValidationError(
                _('No lines have been imported, check the file'))
        self.write({'state': 'step_done'})
        return self._reopen_view()
