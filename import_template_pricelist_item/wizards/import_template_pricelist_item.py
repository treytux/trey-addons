###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplatePricelistItem(models.TransientModel):
    _name = 'import.template.pricelist.item'
    _description = 'Template for import pricelist item file'

    def field_get_or_create(self, model, name, search_field, is_required):
        errors = []
        model_name = self.env[model]._description
        if not name:
            if is_required:
                errors.append(_('%s %s not found.') % (model_name, name))
            return None, errors
        model_obj = self.env[model]
        records = model_obj.search([
            (search_field, '=', name),
        ])
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

    def purchase_pricelist_id_get_or_create(self, pricelist_name):
        return self.field_get_or_create(
            'product.pricelist.purchase', pricelist_name, 'name', True)

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

    def product_brand_id_get_or_create(self, name):
        return self.field_get_or_create('product.brand', name, 'name', False)

    def product_season_id_get_or_create(self, name):
        return self.field_get_or_create('product.season', name, 'name', False)

    def base_pricelist_id_get_or_create(self, name):
        return self.field_get_or_create(
            'product.pricelist', name, 'name', False)

    def cumulative_discount_line_get(self, df, row):
        def get_disc_values(values):
            if not values:
                return {}, []
            errors = []
            disc_list = [v.strip() for v in values.split(';')]
            disc_percent = [v.strip() for v in disc_list[0].split('+')]
            disc_texts = [v.strip() for v in disc_list[1].split(',')]
            if len(disc_percent) != len(disc_texts):
                errors.append(_(
                    'You must indicate the same number of accumulated '
                    'discounts as of texts associated with them.'))
            return dict(zip(disc_percent, disc_texts)), errors

        errors = []
        cols = [c for c in df.columns if c.startswith('cumulative_discounts:')]
        if not cols:
            return None, None
        if len(cols) > 1:
            errors.append(_(
                'More than one column found with name '
                '\'cumulative_discounts:\'; there should be only one.'))
            return None, errors
        res = []
        discounts, disc_errors = get_disc_values(row[cols[0]])
        errors.append(disc_errors)
        for percent, text in discounts.items():
            res.append((0, 0, {
                'discount': percent,
                'name': text,
            }))
        return res, errors

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
                elif data[field] == '3_brand':
                    required_fields.append('product_brand_id')
                elif data[field] == '3_season':
                    required_fields.append('product_season_id')
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

    def delete_items(self, data_items):
        pricelist_ids = []
        for data_item in data_items:
            pricelist_ids.append(data_item['purchase_pricelist_id'])
        pricelists = self.env['product.pricelist.purchase'].browse(
            list(set(pricelist_ids)))
        for pricelist in pricelists:
            pricelist.item_ids.unlink()

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != [] and error[1] != [[]]:
                    wizard.error(error[0], error[1][0])

        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, ['purchase_pricelist_id', 'applied_on', 'compute_price'])
        wizard.total_rows = len(df)
        all_errors = []
        orm_errors = False
        items2create = []
        for index, row in df.iterrows():
            wizard.savepoint('import_template_pricelist_item')
            row_index = index + 2
            wizard.step(
                index + 1, 'Import "%s".' % row['purchase_pricelist_id'])
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
            cumul_disc_lines, errors = self.cumulative_discount_line_get(
                df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            if simulation:
                wizard.rollback('import_template_pricelist_item')
                continue
            data['cumulative_discount_ids'] = cumul_disc_lines or None
            row_error = any([
                e for e in all_errors if e[0] == row_index and e[1] != []
                and e[1] != [[]]])
            if row_error:
                wizard.rollback('import_template_pricelist_item')
                continue
            items2create.append(data)
        self.delete_items(items2create)
        for item_data in items2create:
            try:
                self.env['product.pricelist.item'].create(item_data)
                wizard.release('import_template_pricelist_item')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_pricelist_item')
        _add_errors(all_errors)
        return not orm_errors
