###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateSupplierInfo(models.TransientModel):
    _name = 'import.template.supplierinfo'
    _description = 'Template for import supplierinfo file'

    def product_id_get_or_create(self, product_name):
        errors = []
        if not product_name:
            errors.append(_('Product %s not found.') % product_name)
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

    def name_get_or_create(self, supplier_ref):
        errors = []
        if not supplier_ref:
            errors.append(_('Supplier ref %s not found.') % supplier_ref)
            return None, errors
        suppliers = self.env['res.partner'].search([
            ('supplier', '=', True),
            ('ref', '=', supplier_ref),
        ])
        if len(suppliers) > 1:
            errors.append(_(
                'More than one supplier found for %s.') % supplier_ref)
        if not suppliers:
            errors.append(_(
                'The supplier \'%s\' does not exist, select one of the '
                'available ones.') % supplier_ref)
            return None, errors
        return suppliers[0].id, errors

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != []:
                    wizard.error(error[0], error[1][0])

        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, [
                'product_id', 'name', 'product_name', 'product_code', 'price',
                'min_qty'
            ])
        wizard.total_rows = len(df)
        supplierinfo_obj = self.env['product.supplierinfo']
        all_errors = []
        orm_errors = False
        for index, row in df.iterrows():
            wizard.savepoint('import_template_supplierinfo')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['product_id'])
            data, errors = wizard.get_data_row(
                self, 'product.supplierinfo', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('product.supplierinfo', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            product = self.env['product.product'].browse(data['product_id'])
            data['product_tmpl_id'] = (
                product and product.product_tmpl_id
                and product.product_tmpl_id.id or None)
            if simulation:
                wizard.rollback('import_template_supplierinfo')
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                wizard.rollback('import_template_supplierinfo')
                continue
            supplierinfos = supplierinfo_obj.search([
                ('name', '=', data['name']),
                ('product_id', '=', data['product_id']),
            ])
            try:
                if supplierinfos:
                    supplierinfos.write(data)
                else:
                    supplierinfos.create(data)
                wizard.release('import_template_supplierinfo')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_supplierinfo')
        _add_errors(all_errors)
        return not orm_errors
