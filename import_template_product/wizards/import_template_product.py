###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from itertools import permutations

import requests
from odoo import _, models


class ImportTemplateProduct(models.TransientModel):
    _name = 'import.template.product'
    _description = 'Template for import product file'

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

    def attributes_line_get(self, df, row):
        def list_attr_values(values):
            return [v.strip() for v in str(values).split(',')]

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

    def get_image_variant(self, product, df, row):
        cols = [c for c in df.columns if c.startswith('image_variant:')]
        for c in cols:
            if row[c] is None:
                continue
            for value in row[c].split(';'):
                values = value.split()
                url_variant = values[-1]
                for variant_vals in values[:-1]:
                    variant_vals = variant_vals.replace(
                        ',', '').replace(';', '').replace(':', '')
                    attr_vals = variant_vals.split('-')
                    perms = permutations(
                        product.attribute_value_ids.mapped('name'))
                    for perm in list(perms):
                        if attr_vals == list(perm):
                            return url_variant
        return None

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

    def check_product_barcode_unique(self, barcode):
        errors = []
        if barcode is None:
            return errors
        barcodes = self.env['product.template'].search([
            ('barcode', '=', int(barcode)),
        ])
        if len(barcodes) > 0:
            errors.append(_('duplicate key value violates unique constraint '
                            '"product_product_barcode_uniq". '
                            'Key (barcode)=(%i) already exists.') % barcode)
        return errors

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
                'default_code', 'name', 'categ_id', 'type', 'sale_ok',
                'purchase_ok', 'standard_price', 'list_price', 'invoice_policy'
            ])
        wizard.total_rows = len(df)
        product_tmpl_obj = self.env['product.template']
        supplierinfo_obj = self.env['product.supplierinfo']
        all_errors = []
        all_warns = []
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
            if 'barcode' in row:
                errors = self.check_product_barcode_unique(row['barcode'])
                for error in errors:
                    all_errors.append((row_index, [error]))
            attr_lines, errors = self.attributes_line_get(df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            if row.get('image', None):
                images, warns = self.images_get(row['image'])
                for warn in warns:
                    all_warns.append((row_index, [warn]))
                image = images and images[0] or None
                data.update({
                    'image': image,
                    'product_image_ids': [(6, 0, [])],
                })
                data['product_image_ids'] += [
                    (0, 0, {'image': i}) for i in images
                ]
            else:
                data.update({
                    'image': None,
                    'product_image_ids': [(6, 0, [])],
                })
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
                '|',
                ('active', '=', False),
                ('active', '=', True),
                ('default_code', '=', data['default_code']),
            ])
            if not tmpls and row.get('supplier_ref:'):
                info = supplierinfo_obj.search([
                    ('name.ref', '=', row.get('supplier_ref:')),
                    ('product_code', '=', data['default_code']),
                ])
                if info:
                    tmpls = info[0].product_tmpl_id
            try:
                if 'barcode' in data and data['barcode'] == '':
                    del data['barcode']
                if ('invoice_policy' in data
                        and data['invoice_policy'] is False):
                    del data['invoice_policy']
                if tmpls:
                    if tmpls.attribute_line_ids:
                        data.pop('attribute_line_ids')
                        warn_msg = _(
                            'The product template with default_code \'%s\' '
                            'already had variant attributes. Review it, they '
                            'have not been overwritten.') % (
                                data['default_code'])
                        all_warns.append((row_index, [warn_msg]))
                    tmpls.write(data)
                    for product in tmpls.product_variant_ids:
                        product.standard_price = data['standard_price']
                        if 'weight' in data:
                            product.weight = data['weight']
                        url_image = self.get_image_variant(product, df, row)
                        if url_image:
                            images, warns = self.images_get(url_image)
                            for warn in warns:
                                all_warns.append((row_index, [warn]))
                            if images:
                                product.image_variant = images[0]
                        else:
                            product.image_variant = None
                else:
                    product_tmpl = tmpls.create(data)
                    for product in product_tmpl.product_variant_ids:
                        product.standard_price = data['standard_price']
                        if 'weight' in data:
                            product.weight = data['weight']
                        url_image = self.get_image_variant(product, df, row)
                        if url_image:
                            images, warns = self.images_get(url_image)
                            for warn in warns:
                                all_warns.append((row_index, [warn]))
                            if images:
                                product.image_variant = images[0]
                wizard.release('import_template')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template')
        _add_errors(all_errors)
        _add_warns(all_warns)
        return not orm_errors
