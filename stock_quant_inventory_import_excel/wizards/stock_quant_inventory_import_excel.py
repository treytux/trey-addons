###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_log = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    _log.debug('You need to install pandas library, use `pip3 install pandas`')


class StockQuantInventoryImportExcel(models.TransientModel):
    _name = 'stock.quant.inventory_import_excel'
    _description = 'Stock quant inventory import excel'

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
    )
    filename = fields.Char(
        string='Filename',
    )
    file = fields.Binary(
        string='File',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('error', 'Error'),
            ('ok', 'Ok'),
        ],
        string='State',
        default='draft',
    )
    error_ids = fields.One2many(
        comodel_name='stock.quant.inventory_import_excel.error',
        inverse_name='wizard_id',
        string='Errors',
    )

    def _reopen_view(self):
        action = self.env.ref(
            'stock_quant_inventory_import_excel'
            '.stock_quant_inventory_import_excel_action').read()[0]
        action['res_id'] = self.id
        return action

    def action_back(self):
        self.ensure_one()
        self.state = 'draft'
        self.error_ids.unlink()
        return self._reopen_view()

    def add_error(self, message):
        self.ensure_one()
        if self.error_ids.filtered(lambda e: e.name == message):
            return False
        self.error_ids.create({
            'wizard_id': self.id,
            'name': message,
        })
        return True

    def get_rows(self):
        self.ensure_one()
        file_content = base64.b64decode(self.file)
        df = pd.read_excel(io.BytesIO(file_content), dtype={'EAN': str})
        if 'EAN' not in df.columns:
            self.add_error(_('EAN column not found in the file'))
            return []
        product_obj = self.env['product.product']
        df = df.dropna(subset=['EAN'])
        if 'CANTIDAD' not in df.columns:
            df['CANTIDAD'] = 1
        df['CANTIDAD'] = df['CANTIDAD'].fillna(1)
        df = df.groupby('EAN', as_index=False).agg({'CANTIDAD': 'sum'})
        result = []
        for index, row in df.iterrows():
            ean = row['EAN']
            quantity = row['CANTIDAD']
            if isinstance(quantity, str):
                raise UserError(_(
                    'Invalid quantity in row %s. Use a numeric value and try '
                    'again.') % (index + 2)
                )
            if pd.isna(ean):
                continue
            _log.info(
                f'[{index + 1}/{len(df)}] Processing EAN {ean} with '
                f'quantity {quantity}')
            product = product_obj.search([('barcode', '=', ean)])
            if not product:
                self.add_error(_('EAN %s not found in products') % ean)
                continue
            result.append(row)
        return result

    def action_check_file(self):
        self.ensure_one()
        if not self.filename or not self.filename.lower().endswith('.xlsx'):
            raise UserError(_('The file must have an .xlsx extension'))
        self.error_ids.unlink()
        self.get_rows()
        self.state = 'error' if self.error_ids else 'ok'
        return self._reopen_view()

    def import_inventory(self):
        self.ensure_one()
        product_obj = self.env['product.product']
        quant_obj = self.env['stock.quant']
        rows = self.get_rows()
        for index, row in enumerate(rows, start=1):
            ean = row['EAN']
            quantity = row['CANTIDAD']
            product = product_obj.search([('barcode', '=', ean)])
            line = quant_obj.search([
                ('location_id', '=', self.location_id.id),
                ('product_id', '=', product.id),
            ], limit=1)
            if line:
                line.inventory_quantity = quantity
            else:
                line = quant_obj.create({
                    'location_id': self.location_id.id,
                    'product_id': product.id,
                    'inventory_quantity': quantity,
                })
            line.action_apply_inventory()
            _log.info(f'{index}/{len(rows)} Product with EAN {ean} processed')


class StockQuantInventoryImportExcelError(models.TransientModel):
    _name = 'stock.quant.inventory_import_excel.error'
    _description = 'Stock quant inventory import excel error'

    wizard_id = fields.Many2one(
        comodel_name='stock.quant.inventory_import_excel',
        string='Wizard',
    )
    name = fields.Char(
        string='Error',
    )
