###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from itertools import permutations

import requests
from odoo import _, models


class ImportTemplateProductVariant(models.TransientModel):
    _name = 'import.template.product.variant'
    _description = 'Template for import product variant file'

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

    def _get_uom(self, uom_name):
        errors = []
        if not uom_name:
            errors.append(_('Uom %s not found.') % uom_name)
            return None, errors
        uoms = self.env['uom.uom'].search([
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

    def uom_id_get_or_create(self, uom_name):
        return self._get_uom(uom_name)

    def uom_po_id_get_or_create(self, uom_name):
        return self._get_uom(uom_name)

    def product_brand_id_get_or_create(self, brand_name):
        errors = []
        if not brand_name:
            return None, errors
        brands = self.env['product.brand'].search([
            ('name', '=', brand_name)
        ])
        if len(brands) > 1:
            errors.append(_(
                'More than one product brand found for %s.') % brand_name)
        if not brands:
            errors.append(_(
                'The product brand \'%s\' does not exist, select one of the '
                'available ones.') % brand_name)
            return None, errors
        return brands[0].id, errors

    def parse_float_string(self, value):
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
                self.parse_float_string(row[c]))
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

    def images_get(self, url):
        images = []
        warns = []
        if not url:
            return images, warns
        try:
            response = requests.get(url)
            images.append(base64.b64encode(response.content))
        except Exception:
            warns.append(_('Url image not found for %s.') % url)
        return images, warns

    def get_product_tmpl_values(self, df, row):
        data = {}
        no_fields = []
        no_function = []
        all_errors = []
        product_tmpl_fields = self.env['product.template']._fields
        product_tmpl_fields_names = product_tmpl_fields.keys()
        relational_types = ('many2one', 'many2many', 'one2many')
        cols = [c for c in df.columns if c.startswith('*TMPL*')]
        for c in cols:
            if row[c] is None:
                continue
            col = c.replace('*TMPL*', '')
            if col in product_tmpl_fields_names:
                if product_tmpl_fields[col].type not in relational_types:
                    data[col] = row[c]
                    continue
                method_name = '%s_get_or_create' % col
                if hasattr(self, method_name):
                    fnc = getattr(self, method_name)
                    id, errors = fnc(row[c])
                    for error in errors:
                        all_errors.append(error)
                    data[col] = id
                else:
                    no_function.append(col)
        msg = _('The \'%s\' column is not a field for model.')
        for n in no_fields:
            all_errors.append(msg % n)
        msg = _(
            'The \'%s\' column is a relational field and there is no defined '
            'function to convert it.')
        for n in no_function:
            all_errors.append(msg % n)
        return data, all_errors

    def find_products(self, tmpls, products, attr_values, variant_found):
        for product in tmpls.product_variant_ids:
            if variant_found is True:
                break
            perms = permutations(
                product.attribute_value_ids.mapped('name'))
            for perm in list(perms):
                if list(perm) == list(attr_values):
                    products = product
                    variant_found = True
                    break
        return products, variant_found

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
                'product_tmpl_code', 'name', 'categ_id', 'type', 'uom_id',
                'uom_po_id', 'default_code', 'barcode'
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
            product_tmpl_data, errors = self.get_product_tmpl_values(
                df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            product_tmpl_data, errors = wizard.parser(
                'product.template', product_tmpl_data)
            for error in errors:
                all_errors.append((row_index, [error]))
            if simulation:
                wizard.rollback('import_template')
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                wizard.rollback('import_template')
                continue
            if product_tmpl_data.get('image', None):
                images, warns = self.images_get(product_tmpl_data['image'])
                for warn in warns:
                    all_warns.append((row_index, [warn]))
                image = images and images[0] or None
                product_tmpl_data.update({
                    'image': image,
                    'product_image_ids': [(6, 0, [])],
                })
                product_tmpl_data['product_image_ids'] += [
                    (0, 0, {'image': i}) for i in images
                ]
            else:
                product_tmpl_data.update({
                    'image': None,
                    'product_image_ids': [(6, 0, [])],
                })
            tmpls = product_tmpl_obj.search([
                ('product_tmpl_code', '=', data['product_tmpl_code']),
            ])
            variant_found = False
            try:
                products = self.env['product.product']
                if tmpls:
                    tmpls.write(product_tmpl_data)
                    products, variant_found = self.find_products(
                        tmpls, products, attrs.values(), variant_found)
                    if products:
                        if 'image_variant' in data:
                            images, warns = self.images_get(
                                data['image_variant'])
                            for warn in warns:
                                all_warns.append((row_index, [warn]))
                            data['image_variant'] = (
                                images and images[0] or None)
                        products.write(data)
                    else:
                        attr_values_no_variant, errors = (
                            self.create_attr_or_value(tmpls, attrs))
                        for error in errors:
                            all_errors.append((row_index, [error]))
                        if not errors:
                            tmpls.create_variant_ids()
                            products, variant_found = self.find_products(
                                tmpls, products, attr_values_no_variant,
                                variant_found)
                            if 'image_variant' in data:
                                images, warns = self.images_get(
                                    data['image_variant'])
                                for warn in warns:
                                    all_warns.append((row_index, [warn]))
                                data['image_variant'] = (
                                    images and images[0] or None)
                            products.write(data)
                else:
                    image_variant = None
                    if 'image_variant' in data:
                        images, warns = self.images_get(
                            data['image_variant'])
                        for warn in warns:
                            all_warns.append((row_index, [warn]))
                        image_variant = images and images[0] or None
                        del data['image_variant']
                    data.update(product_tmpl_data)
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
                        products, variant_found = self.find_products(
                            tmpls, products, attr_values_no_variant,
                            variant_found)
                        products.write(data)
                        if image_variant:
                            products.write({
                                'image_variant': image_variant,
                            })
                wizard.release('import_template')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template')
        _add_errors(all_errors)
        _add_warns(all_warns)
        return not orm_errors
