###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from itertools import permutations

from odoo import _, models


class ImportTemplateProductVariant(models.TransientModel):
    _name = 'import.template.product.variant'
    _description = 'Template for import product variant file'

    def parse_float(self, value):
        try:
            if value == int(value):
                return str(int(value))
            else:
                return str(value)
        except Exception:
            return value

    def attributes_values_get(self, df, row):
        cols = [c for c in df.columns if c.startswith('attribute:')]
        attrs = {}
        for c in cols:
            if row[c] is None:
                continue
            attrs[c.replace('attribute:', '').strip()] = (
                self.parse_float(row[c]))
        return attrs, list(attrs.values())

    def create_attr_or_value(self, tmpls, attrs):
        errors = []
        attr_values_no_variant = []
        attr_obj = self.env['product.attribute']
        attr_names = list(attrs.keys())
        for attr_name in attr_names:
            attributes = attr_obj.search([
                ('name', '=', attr_name),
            ])
            if not attributes:
                attributes = attr_obj.create({
                    'name': attr_name,
                })
            if (
                    attributes.create_variant != 'no_variant'
                    and not self.env.context.get('creating_product_tmpl')):
                template_attrs = [
                    (ln.attribute_id.name) for ln in tmpls.attribute_line_ids]
                if attr_name not in template_attrs:
                    errors.append(_(
                        'The \'%s\' attribute of the file does not match the '
                        'attributes of the product template; you must review '
                        'it.') % attr_name)
                    continue
            if not tmpls.attribute_line_ids.filtered(
                    lambda ln: ln.attribute_id == attributes):
                attr2create_id = attributes.id
            attr_value = attributes.value_ids.filtered(
                lambda v: v.name == attrs[attr_name])
            if not attr_value:
                attr_value = attributes.value_ids.create({
                    'name': attrs[attr_name],
                    'attribute_id': attributes.id,
                })
            if not tmpls.attribute_line_ids.filtered(
                    lambda ln: ln.attribute_id == attributes
                    and attr_value in ln.value_ids):
                if attributes not in tmpls.attribute_line_ids.mapped(
                        'attribute_id'):
                    self.env['product.template.attribute.line'].create({
                        'product_tmpl_id': tmpls.id,
                        'attribute_id': attr2create_id,
                        'value_ids': [(4, attr_value.id)],
                    })
                else:
                    attr_line = tmpls.attribute_line_ids.filtered(
                        lambda ln: ln.attribute_id == attributes)
                    attr_line.write({
                        'value_ids': [(4, attr_value.id)],
                    })
            if attributes.create_variant != 'no_variant':
                attr_values_no_variant.append(attr_value.name)
        return attr_values_no_variant, errors

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != []:
                    wizard.error(error[0], error[1][0])

        def _add_warns(warns):
            for warn in warns:
                if warn != [] and warn[1] != []:
                    wizard.warn(warn[0], warn[1][0])

        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, [
                'product_tmpl_code',
            ])
        wizard.total_rows = len(df)
        product_tmpl_obj = self.env['product.template']
        all_errors = []
        all_warns = []
        orm_errors = False
        for index, row in df.iterrows():
            wizard.savepoint('import_template')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['product_tmpl_code'])
            data, errors = wizard.get_data_row(
                self, 'product.product', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('product.product', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            attrs, attr_values = self.attributes_values_get(df, row)
            if simulation:
                wizard.rollback('import_template')
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                wizard.rollback('import_template')
                continue
            tmpls = product_tmpl_obj.search([
                ('product_tmpl_code', '=', data['product_tmpl_code']),
            ])
            variant_found = False
            try:
                products = self.env['product.product']
                if tmpls:
                    for product in tmpls.product_variant_ids:
                        if variant_found is True:
                            break
                        perms = permutations(
                            product.attribute_value_ids.mapped('name'))
                        for perm in list(perms):
                            if list(perm) == list(attrs.values()):
                                products = product
                                variant_found = True
                                break
                    if products:
                        products.write(data)
                    else:
                        attr_values_no_variant, errors = (
                            self.create_attr_or_value(tmpls, attrs))
                        for error in errors:
                            all_errors.append((row_index, [error]))
                        if not errors:
                            tmpls.create_variant_ids()
                            for product in tmpls.product_variant_ids:
                                if variant_found is True:
                                    break
                                perms = permutations(
                                    product.attribute_value_ids.mapped('name'))
                                for perm in list(perms):
                                    if list(perm) == list(
                                            attr_values_no_variant):
                                        products = product
                                        variant_found = True
                                        break
                            products.write(data)
                else:
                    data['name'] = data['product_tmpl_code']
                    tmpls = tmpls.create(data)
                    attr_values_no_variant, errors = (
                        self.with_context(
                            creating_product_tmpl=True
                        ).create_attr_or_value(tmpls, attrs))
                    for error in errors:
                        all_errors.append((row_index, [error]))
                    if not errors:
                        tmpls.create_variant_ids()
                        for product in tmpls.product_variant_ids:
                            if variant_found is True:
                                break
                            perms = permutations(
                                product.attribute_value_ids.mapped('name'))
                            for perm in list(perms):
                                if list(perm) == list(attr_values_no_variant):
                                    products = product
                                    variant_found = True
                                    break
                        products.write(data)
                wizard.release('import_template')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template')
        _add_errors(all_errors)
        _add_warns(all_warns)
        return not orm_errors
