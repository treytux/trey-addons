###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import math

from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductCatalogImport(models.TransientModel):
    _name = 'product.catalog.import'
    _description = 'Import product catalog'

    file = fields.Binary(
        string='Excel file',
        required=True,
    )
    file_name = fields.Char(
        string='Filename',
    )
    line_ids = fields.Many2many(
        'product.catalog.line',
        string='Created lines',
    )
    total_lines = fields.Integer(
        string='Total lines',
        readonly=True,
    )
    processed_lines = fields.Integer(
        string='Processed lines',
        readonly=True,
    )

    def _dataframe(self):
        try:
            import pandas as pd
        except ImportError:
            raise UserError(_('The Python package pandas is required.'))
        extension = (self.file_name or '').lower().rsplit('.', 1)[-1]
        if extension not in ('xls', 'xlsx'):
            raise UserError(_('Only Excel files are supported.'))
        buffer = io.BytesIO(base64.b64decode(self.file))
        engine = 'openpyxl' if extension == 'xlsx' else 'xlrd'
        return pd.read_excel(buffer, engine=engine).where(
            lambda value: value.notna(), None)

    @staticmethod
    def _native_value(value):
        if hasattr(value, 'item'):
            value = value.item()
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    def action_import(self):
        self.ensure_one()
        dataframe = self._dataframe()
        line_obj = self.env['product.catalog.line']
        created = self.env['product.catalog.line']
        self.total_lines = len(dataframe)
        for start in range(0, len(dataframe), 1000):
            chunk = dataframe.iloc[start:start + 1000]
            for offset, row in chunk.iterrows():
                values = {
                    key: self._native_value(value)
                    for key, value in row.to_dict().items()
                    if value is not None
                }
                values['line_num'] = int(offset) + 2
                values['product_code'] = line_obj._product_code(values)
                values['source_data'] = values.copy()
                line_values = {
                    key: value for key, value in values.items()
                    if key in line_obj._fields
                }
                existing = line_obj.search([
                    ('line_num', '=', values['line_num'])
                ], limit=1)
                if existing:
                    existing.write(line_values)
                    created |= existing
                else:
                    created |= line_obj.create_from_row(line_values)
            self.env.cr.commit()
            self.processed_lines = min(start + 1000, len(dataframe))
        self.line_ids = [(6, 0, created.ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Catalog lines'),
            'res_model': 'product.catalog.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created.ids)],
        }
