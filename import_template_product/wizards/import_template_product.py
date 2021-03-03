# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import _, api, models


class ImportTemplateProduct(models.TransientModel):
    _name = 'import.template.product'
    _description = 'Template for import product file'

    @api.multi
    def categ_id_get_or_create(self, category):
        def _get_or_create_parent(cat_name, parent_id):
            errors = []
            categs = self.env['product.category'].search([
                ('name', '=', cat_name),
                ('parent_id', '=', parent_id),
            ])
            if len(categs) > 1:
                errors.append(_(
                    'More than one category found for %s.') % cat_name)
            if not categs:
                categs = self.env['product.category'].create({
                    'name': cat_name,
                    'parent_id': parent_id,
                })
            return categs[0].id, errors

        errors = []
        if not category:
            errors.append(_('Category %s not found.') % category)
            return None, errors
        parent_id = None
        categories = category.split('/')
        for cat in categories:
            parent_id, errors = _get_or_create_parent(cat, parent_id)
        return parent_id, errors

    @api.multi
    def _get_uom(self, uom_name):
        errors = []
        if not uom_name:
            errors.append(_('Uom %s not found.') % uom_name)
            return None, errors
        uoms = self.env['product.uom'].search([
            ('name', '=', uom_name)
        ])
        if len(uoms) > 1:
            errors.append(_(
                'More than one product uom found for %s.') % uom_name)
        if not uoms:
            errors.append(_(
                'The unit of measure \'%s\' does not exist, select one of the '
                'available ones.') % uom_name)
            return None, errors
        return uoms[0].id, errors

    @api.multi
    def uom_id_get_or_create(self, uom_name):
        return self._get_uom(uom_name)

    @api.multi
    def uom_po_id_get_or_create(self, uom_name):
        return self._get_uom(uom_name)

    @api.multi
    def attributes_line_get(self, df, row):
        def list_attr_values(values):
            return [v.strip() for v in values.split(',')]

        def attr_value_id_get_or_create(attr, value_name):
            value = attr.value_ids.filtered(lambda v: v.name == value_name)
            if not value:
                value = attr.value_ids.create({
                    'name': value_name,
                    'attribute_id': attr.id,
                })
            return value.id

        cols = [c for c in df.columns if c.startswith('attribute:')]
        attrs = {}
        for c in cols:
            if row[c] is None:
                continue
            attrs[c.replace(
                'attribute:', '').strip()] = list_attr_values(row[c])
        res = []
        errors = []
        attr_obj = self.env['product.attribute']
        for attr, vals in attrs.items():
            attrs = attr_obj.search([('name', '=', attr)])
            if not attrs:
                attrs = attr_obj.create({'name': attr})
            if len(attrs) > 1:
                errors.append(_(
                    'More than one attribute found for %s.') % attr)
                continue
            res.append((0, 0, {
                'attribute_id': attrs.id,
                'value_ids': [
                    (6, 0, [attr_value_id_get_or_create(attrs, v)
                        for v in vals])
                ]
            }))
        return res, errors

    @api.multi
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
                'default_code', 'name', 'categ_id', 'type', 'sale_ok',
                'purchase_ok', 'standard_price', 'list_price'
            ])
        wizard.total_rows = len(df)
        product_tmpl_obj = self.env['product.template']
        all_errors = []
        orm_errors = False
        for index, row in df.iterrows():
            wizard.savepoint('import_template')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['default_code'])
            data, errors = wizard.get_data_row(
                self, 'product.template', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('product.template', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            attr_lines, errors = self.attributes_line_get(df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            if simulation:
                wizard.rollback('import_template')
                continue
            data['attribute_line_ids'] = attr_lines or None
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                wizard.rollback('import_template')
                continue
            tmpls = product_tmpl_obj.search([
                ('default_code', '=', data['default_code']),
            ])
            try:
                if tmpls:
                    tmpls.write(data)
                    for product in tmpls.product_variant_ids:
                        product.standard_price = data['standard_price']
                else:
                    product_tmpl = tmpls.create(data)
                    for product in product_tmpl.product_variant_ids:
                        product.standard_price = data['standard_price']
                wizard.release('import_template')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template')
        _add_errors(all_errors)
        return not orm_errors
