###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateCustomerInfo(models.TransientModel):
    _name = 'import.template.customerinfo'
    _description = 'Template for import customerinfo file'

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

    def name_get_or_create(self, customer_ref):
        errors = []
        if not customer_ref:
            errors.append(_('Customer ref %s not found.') % customer_ref)
            return None, errors
        customers = self.env['res.partner'].search([
            ('customer', '=', True),
            ('ref', '=', customer_ref),
        ])
        if len(customers) > 1:
            errors.append(_(
                'More than one customer found for %s.') % customer_ref)
        if not customers:
            errors.append(_(
                'The customer \'%s\' does not exist, select one of the '
                'available ones.') % customer_ref)
            return None, errors
        return customers[0].id, errors

    def process_relational_fields(self, df, row):
        customerinfo_fields = self.env['product.customerinfo']._fields
        customerinfo_fields_names = customerinfo_fields.keys()
        relational_types = ('many2one', 'many2many', 'one2many')
        cols = [c for c in df.columns]
        res_dict = {}
        errors = []
        for col in cols:
            if col in customerinfo_fields_names:
                if customerinfo_fields[col].type not in relational_types:
                    continue
                method_name = 'process_relational_field_%s' % col
                if hasattr(self, method_name):
                    fnc = getattr(self, method_name)
                    res_aux, errors_aux = fnc(col, row[col])
                    res_dict[col] = res_aux
                    errors.append(errors_aux)
        return res_dict, errors

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
        customerinfo_obj = self.env['product.customerinfo']
        all_errors = []
        orm_errors = False
        for index, row in df.iterrows():
            wizard.savepoint('import_template_customerinfo')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['product_id'])
            data, errors = wizard.get_data_row(
                self, 'product.customerinfo', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('product.customerinfo', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            product = self.env['product.product'].browse(data['product_id'])
            data['product_tmpl_id'] = (
                product and product.product_tmpl_id
                and product.product_tmpl_id.id or None)
            res_dict, errors = self.process_relational_fields(df, row)
            for error in errors:
                if error != []:
                    all_errors.append((row_index, error))
            for field_rel, vals in res_dict.items():
                data[field_rel] = (
                    vals and [(6, 0, [v for v in vals])] or [(6, 0, [])])
            if simulation:
                wizard.rollback('import_template_customerinfo')
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                wizard.rollback('import_template_customerinfo')
                continue
            if len(product.product_tmpl_id.product_variant_ids) == 1:
                customerinfos = customerinfo_obj.search([
                    ('name', '=', data['name']),
                    ('product_tmpl_id', '=', data['product_tmpl_id']),
                ])
                del data['product_id']
            else:
                customerinfos = customerinfo_obj.search([
                    ('name', '=', data['name']),
                    ('product_tmpl_id', '=', data['product_tmpl_id']),
                    ('product_id', '=', data['product_id']),
                ])
            try:
                if customerinfos:
                    customerinfos.write(data)
                else:
                    customerinfos.create(data)
                wizard.release('import_template_customerinfo')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_customerinfo')
        _add_errors(all_errors)
        return not orm_errors
