###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateSalePricelistItem(models.TransientModel):
    _name = 'import.template.sale.pricelist.item'
    _description = 'Template for import pricelist item file'

    def get_field_domain(self, search_field, name):
        return [(search_field, '=', name)]

    def field_get_or_create(self, model, name, search_field, is_required):
        errors = []
        model_name = self.env[model]._description
        if not name:
            if is_required:
                errors.append(_('%s %s not found.') % (model_name, name))
            return None, errors
        model_obj = self.env[model]
        records = model_obj.search(self.get_field_domain(search_field, name))
        if len(records) > 1:
            errors.append(_(
                'More than one %s found for %s.') % (model_name, name))
        if not records:
            if is_required:
                records = model_obj.create({
                    search_field: name,
                })
            else:
                errors.append(_('%s %s not found.') % (model_name, name))
                return None, errors
        return records[0].id, errors

    def pricelist_id_get_or_create(self, pricelist_name):
        return self.field_get_or_create(
            'product.pricelist', pricelist_name, 'name', True)

    def categ_id_get_or_create(self, category):
        def _get_parent(cat_name, parent_id):
            errors = []
            categs = self.env['product.category'].search([
                ('name', '=', cat_name),
                ('parent_id', '=', parent_id),
            ])
            if len(categs) > 1:
                errors.append(_(
                    'More than one category found for %s.') % cat_name)
            if not categs:
                errors.append(_('Category %s not found.') % category)
                return None, errors
            return categs[0].id, errors

        errors = []
        if not category:
            return None, errors
        parent_id = None
        categories = category.split('/')
        for cat in categories:
            parent_id, errors = _get_parent(cat, parent_id)
        return parent_id, errors

    def parse_float(self, value):
        try:
            if value and value == int(value):
                value = int(value)
        except Exception:
            value = value
        return value

    def product_tmpl_id_get_or_create(self, default_code):
        default_code = self.parse_float(default_code)
        return self.field_get_or_create(
            'product.template', default_code, 'default_code', False)

    def product_id_get_or_create(self, default_code):
        default_code = self.parse_float(default_code)
        return self.field_get_or_create(
            'product.product', default_code, 'default_code', False)

    def base_pricelist_id_get_or_create(self, name):
        return self.field_get_or_create(
            'product.pricelist', name, 'name', False)

    def check_required_fields(self, required_fields, data):
        errors = []
        msg = _('The \'%s\' field is required.')
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == 0.0:
                errors.append(msg % field)
        return errors

    def check_relational_fields(self, fields, data):
        required_fields = []
        errors = []
        for field in fields:
            error_msg = _(
                'Option \'%s\' for \'%s\' does not exist. You must '
                'choose a valid value.' % (data[field], field))
            if field == 'applied_on':
                if data[field] == '3_global':
                    continue
                elif data[field] == '2_product_category':
                    required_fields.append('categ_id')
                elif data[field] == '1_product':
                    required_fields.append('product_tmpl_id')
                elif data[field] == '0_product_variant':
                    required_fields.append('product_id')
                else:
                    errors.append(error_msg)
            elif field == 'compute_price':
                if data[field] == 'fixed':
                    required_fields.append('fixed_price')
                elif data[field] == 'percentage':
                    required_fields.append('percent_price')
                elif data[field] == 'formula':
                    required_fields.append('base')
                else:
                    errors.append(error_msg)
            elif field == 'base' and data[field] == 'pricelist':
                required_fields.append('base_pricelist_id')
        errors += self.check_required_fields(required_fields, data)
        return errors

    def get_pricelist_item_domain(self, data):
        domain = [
            ('applied_on', '=', data['applied_on']),
            ('pricelist_id', '=', data['pricelist_id']),
            ('min_quantity', '=', data['min_quantity']),
        ]
        if data.get('date_start', False):
            domain.append(('date_start', '=', data['date_start']))
        if data.get('date_end', False):
            domain.append(('date_end', '=', data['date_end']))
        if data['applied_on'] == '2_product_category':
            domain.append(('categ_id', '=', data['categ_id']))
        elif data['applied_on'] == '1_product':
            domain.append(('product_tmpl_id', '=', data['product_tmpl_id']))
        elif data['applied_on'] == '0_product_variant':
            domain.append(('product_id', '=', data['product_id']))
        return domain

    def search_items2update(self, data, row_index, simulation):
        errors = []
        pricelist_to_update = {}
        pricelist_item_obj = self.env['product.pricelist.item']
        pricelists = pricelist_item_obj.search(
            self.get_pricelist_item_domain(data))
        if len(pricelists) > 1:
            errors.append(_('Multiple pricelist items found'))
        elif len(pricelists) == 1 and not simulation:
            pricelist_to_update = {pricelists.id: data}
        return pricelist_to_update, errors

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != [] and error[1] != [[]]:
                    wizard.error(error[0], error[1][0])

        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, ['pricelist_id', 'applied_on', 'compute_price'])
        wizard.total_rows = len(df)
        all_errors = []
        orm_errors = False
        items2create = []
        items2update = []
        for index, row in df.iterrows():
            wizard.savepoint('import_template_sale_pricelist_item')
            row_index = index + 2
            wizard.step(
                index + 1, 'Import "%s".' % row['pricelist_id'])
            data, errors = wizard.get_data_row(
                self, 'product.pricelist.item', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('product.pricelist.item', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            errors = self.check_relational_fields(
                ['applied_on', 'compute_price', 'base'], data)
            for error in errors:
                all_errors.append((row_index, [error]))
            item2update, errors = self.search_items2update(
                data, row_index, simulation)
            for error in errors:
                all_errors.append((row_index, [error]))
            if simulation:
                wizard.rollback('import_template_sale_pricelist_item')
                continue
            row_error = any([
                e for e in all_errors if e[0] == row_index and e[1] != []
                and e[1] != [[]]])
            if row_error:
                wizard.rollback('import_template_sale_pricelist_item')
                continue
            if not item2update:
                items2create.append(data)
            else:
                items2update.append(item2update)
        pricelist_item_obj = self.env['product.pricelist.item']
        for item_data in items2create:
            try:
                pricelist_item_obj.create(item_data)
                wizard.release('import_template_sale_pricelist_item')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_sale_pricelist_item')
        for item2update in items2update:
            for key, item_data in item2update.items():
                try:
                    pricelist_item = pricelist_item_obj.browse(key)
                    pricelist_item.write(item_data)
                    wizard.release('import_template_sale_pricelist_item')
                except Exception as e:
                    orm_errors = True
                    all_errors.append((row_index, [e]))
                    wizard.rollback('import_template_sale_pricelist_item')
        _add_errors(all_errors)
        return not orm_errors
