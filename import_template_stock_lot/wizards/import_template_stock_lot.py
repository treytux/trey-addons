###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateStockLot(models.TransientModel):
    _name = 'import.template.stock_lot'
    _description = 'Template for import stock lot file'

    def product_id_get_or_create(self, product_name):
        errors = []
        if not product_name:
            errors.append(_('Product \'%s\' not found.') % product_name)
            return None, errors
        products = self.env['product.product'].search([
            '|',
            ('default_code', '=', product_name),
            ('barcode', '=', product_name),
        ])
        if len(products) > 1:
            errors.append(_(
                'More than one product found for %s.') % product_name)
        if not products:
            errors.append(_(
                'The product \'%s\' does not exist, select one of the '
                'available ones.') % product_name)
            return None, errors
        return products[0].id, errors

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != []:
                    wizard.error(error[0], error[1][0])

        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(df, ['name'])
        wizard.total_rows = len(df)
        stock_lot_obj = self.env['stock.lot']
        all_errors = []
        orm_errors = False
        for index, row in df.iterrows():
            savepoint = self.env.cr.savepoint()
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['name'])
            data, errors = wizard.get_data_row(self, 'stock.lot', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('stock.lot', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            if 'product_id' not in data:
                lots = stock_lot_obj.search([
                    ('name', '=', data['name']),
                ])
                if not lots:
                    error = _(
                        'The lot \'%s\' does not exist, select one of the '
                        'available ones or add a new column \'product_id\' to '
                        'the file with the product\'s default code or '
                        'barcode.') % data['name']
                    all_errors.append((row_index, [error]))
                elif len(lots) > 1:
                    error = _(
                        'More than one lot found for name %s.') % data['name']
                    all_errors.append((row_index, [error]))
                elif len(lots) == 1:
                    data['product_id'] = lots.product_id.id
            if simulation:
                savepoint.rollback()
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                savepoint.rollback()
                continue
            domain = [('name', '=', data['name'])]
            if 'product_id' in data:
                domain.append(('product_id', '=', data['product_id']))
            lots = stock_lot_obj.search(domain)
            try:
                if lots:
                    lots.write(data)
                else:
                    lots.create(data)
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                savepoint.rollback()
        _add_errors(all_errors)
        return not orm_errors
