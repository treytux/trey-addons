###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from itertools import permutations

import requests
from odoo import _, fields, models


class ImportTemplateProductVariant(models.TransientModel):
    _name = 'import.template.product.variant'
    _description = 'Template for import product variant file'

    def categ_id_get_or_create(self, category):
        def _get_parent_categ(cat_name, parent_id, errors):
            categs = self.env['product.category'].search([
                ('name', '=', cat_name),
                ('parent_id', '=', parent_id),
            ])
            if len(categs) > 1:
                errors.append(_(
                    'More than one category found for %s.') % cat_name)
            if not categs:
                errors.append(_('Category not found for %s.') % cat_name)
            return categs and categs[0].id or [], errors

        errors = []
        if not category:
            errors.append(_('Category %s not found.') % category)
            return None, errors
        parent_id = None
        categories = category.split('/')
        for cat in categories:
            category = cat.strip()
            parent_id, errors = _get_parent_categ(category, parent_id, errors)
            if not parent_id:
                break
        return parent_id, errors

    def public_categ_ids_get_or_create(self, category):
        def _get_parent_categ(cat_name, parent_id, errors):
            categs = self.env['product.public.category'].search([
                ('name', '=', cat_name),
                ('parent_id', '=', parent_id),
            ])
            if len(categs) > 1:
                errors.append(_(
                    'More than one category found for %s.') % cat_name)
            if not categs:
                errors.append(_('Web category not found for %s.') % cat_name)
            return categs and categs[0].id or False, errors

        errors = []
        if not category:
            return None, errors
        parent_id = None
        categories = category.split('/')
        for cat in categories:
            category = cat.strip()
            parent_id, errors = _get_parent_categ(category, parent_id, errors)
            if not parent_id:
                break
        return parent_id and [(6, 0, [parent_id])] or None, errors

    def _get_uom(self, uom_name):
        errors = []
        if not uom_name:
            errors.append(_('Uom %s not found.') % uom_name)
            return None, errors
        uoms = self.env['uom.uom'].search([
            ('name', '=', uom_name),
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

    def _get_route(self, route_names):
        errors = []
        route_ids = []
        if not route_names:
            return None, errors
        route_names = str(route_names).strip().split(',')
        route_obj = self.env['stock.route']
        for route_name in route_names:
            route = route_obj.search([
                ('name', 'ilike', route_name),
            ])
            if not route:
                errors.append(
                    _('Stock route not found: \'%s\'') % route_name)
                continue
            if len(route) > 1:
                errors.append(_(
                    'Multiple stock routes found for reference: \'%s\'') % (
                    route_name))
                continue
            route_ids.append(route.id)
        return route_ids, errors

    def uom_id_get_or_create(self, uom_name):
        return self._get_uom(uom_name)

    def uom_po_id_get_or_create(self, uom_name):
        return self._get_uom(uom_name)

    def route_ids_get_or_create(self, route_names):
        return self._get_route(route_names)

    def seller_ids_get_or_create(self, seller_refs):
        errors = []
        supplier_ids = []
        if not seller_refs:
            return None, errors
        seller_refs = str(seller_refs).strip().split(',')
        res_partner_obj = self.env['res.partner']
        for seller_ref in seller_refs:
            supplier = res_partner_obj.search([
                ('ref', '=', seller_ref),
            ])
            if not supplier:
                errors.append(
                    _('Supplier reference not found: \'%s\'') % seller_ref)
                continue
            if len(supplier_ids) > 1:
                errors.append(_(
                    'Multiple suppliers found for reference: \'%s\'') % (
                    seller_ref))
                continue
            supplier_ids.append(supplier.id)
        return supplier_ids, errors

    def product_brand_id_get_or_create(self, brand_name):
        errors = []
        if not brand_name:
            return None, errors
        brands = self.env['product.brand'].search([
            ('name', '=', brand_name),
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
            if row[c] is None or row[c] == '':
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
                    attributes.create_variant == 'no_variant'
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
            if row[c] is None or row[c] == '':
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

    def get_suppliers_data(self, product, supplier_ids, standard_price):
        def append_supplier(seller_id, suppliers_data):
            suppliers_data.append((0, 0, {
                'partner_id': seller_id,
                'price': standard_price,
            }))
            return suppliers_data

        suppliers_data = []
        suppliers_to_del = []
        for seller_id in supplier_ids:
            if not product:
                append_supplier(seller_id, suppliers_data)
            else:
                seller_match = product.seller_ids.filtered(
                    lambda sell: sell.partner_id.id == seller_id)
                if seller_match:
                    suppliers_data.append(
                        (1, seller_match[0].id, {'price': standard_price}))
                    if len(seller_match) > 1:
                        suppliers_to_del += [
                            (3, sm.id) for sm in seller_match[1:]]
                else:
                    append_supplier(seller_id, suppliers_data)
        if suppliers_to_del:
            suppliers_data += suppliers_to_del
        return suppliers_data

    def find_products(self, tmpls, products, attr_values, variant_found):
        for product in tmpls.product_variant_ids:
            if variant_found is True:
                break
            perms = permutations(
                product.product_template_attribute_value_ids.mapped('name'))
            for perm in list(perms):
                if list(perm) == list(attr_values):
                    products = product
                    variant_found = True
                    break
        return products, variant_found

    def format_operations_for_description(self, operations):
        if not operations:
            return '<p>No operations performed</p>'
        result = []
        result.append('<h2>Import Operations Summary</h2>')
        create_ops = [op for op in operations if op['Operation'] == 'CREATE']
        write_ops = [op for op in operations if op['Operation'] == 'WRITE']
        if create_ops:
            result.append('<h3>Created Records</h3>')
            result.append('<ul>')
            for op in create_ops:
                object_str = str(op['Object'])
                parts = object_str.split('(', 1)
                obj_name = parts[0].strip()
                obj_id = 'N/A'
                if len(parts) > 1 and ')' in parts[1]:
                    obj_id = parts[1].split(')', 1)[0].strip(',')
                result.append(
                    f'<li><strong>{obj_name}</strong> (ID: {obj_id})')
                result.append('<ul><li><strong>Values:</strong>')
                result.append('<ul>')
                vals_copy = (
                    op['Vals'].copy() if isinstance(op['Vals'], dict) else {})
                if 'image_1920' in vals_copy:
                    del vals_copy['image_1920']
                if 'image_variant_1920' in vals_copy:
                    del vals_copy['image_variant_1920']
                result.append(f'<li>{vals_copy}</li>')
                result.append('</ul></li></ul></li>')
            result.append('</ul>')
        if write_ops:
            result.append('<h3>Write Records</h3>')
            result.append('<ul>')
            write_by_object = {}
            for op in write_ops:
                obj_key = str(op['Object'])
                if obj_key not in write_by_object:
                    write_by_object[obj_key] = []
                write_by_object[obj_key].append(op)
            for obj_key, ops in write_by_object.items():
                parts = obj_key.split('(', 1)
                obj_name = parts[0].strip()
                obj_id = 'N/A'
                if len(parts) > 1 and ')' in parts[1]:
                    obj_id = parts[1].split(')', 1)[0].strip(',')
                result.append(f'<li><strong>{obj_name}</strong> (ID: {obj_id})')
                result.append('<ul><li><strong>Fields Writed:</strong>')
                result.append('<ul>')
                updated_fields = {}
                for op in ops:
                    if isinstance(op['Vals'], dict):
                        updated_fields.update(op['Vals'])
                if 'image_1920' in updated_fields:
                    del updated_fields['image_1920']
                if 'image_variant_1920' in updated_fields:
                    del updated_fields['image_variant_1920']
                result.append(f'<li>{updated_fields}</li>')
                result.append('</ul></li></ul></li>')
            result.append('</ul>')
        result.append('<p><strong>Import finished successfully.</strong></p>')
        return ''.join(result)

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
        date_start = fields.Datetime.now()
        log = None
        mimetype = (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        operations = []
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, [
                'product_tmpl_code', 'name', 'categ_id', 'type', 'uom_id',
                'uom_po_id', 'default_code', 'barcode',
            ])
        wizard.total_rows = len(df)
        product_tmpl_obj = self.env['product.template']
        all_errors = []
        all_warns = []
        orm_errors = False
        sudo_keys = [
            'categ_id',
            'uom_po_id',
            'uom_id',
        ]
        for index, row in df.iterrows():
            savepoint = self.env.cr.savepoint()
            row_index = index + 2
            if not row.get('product_tmpl_code'):
                error_msg = _(
                    'The \'product_tmpl_code\' field is required, you must fill'
                    ' it with a valid value.')
                all_errors.append((row_index, [error_msg]))
                continue
            product_tmpl_domain = [
                '|', '|',
                ('product_tmpl_code', '=', row['product_tmpl_code']),
                ('default_code', '=', row['product_tmpl_code']),
                ('barcode', '=', row['product_tmpl_code']),
            ]
            tmpls = product_tmpl_obj.search(product_tmpl_domain)
            if not tmpls:
                root_user = self.env.ref('base.user_root')
                tmpls = product_tmpl_obj.with_user(root_user).search(
                    product_tmpl_domain)
            if not tmpls:
                warn_msg = (_(
                    'Product template \'%s\' not found, will be created.') % (
                    row['name']))
                all_warns.append((row_index, [warn_msg]))
            if len(tmpls) > 1:
                error_msg = _(
                    'Multiple products found for reference: \'%s\'') % (
                    row['product_tmpl_code'])
                all_errors.append((row_index, [error_msg]))
            wizard.step(index + 1, 'Import "%s".' % row['product_tmpl_code'])
            data, errors = wizard.get_data_row(
                self, 'product.product', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('product.product', data)
            if 'barcode' in data and not data['barcode']:
                del data['barcode']
            if 'seller_ids' in data and not data['seller_ids']:
                del data['seller_ids']
            if 'route_ids' in data and not data['route_ids']:
                del data['route_ids']
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
                savepoint.rollback()
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                savepoint.rollback()
                continue
            if product_tmpl_data.get('image_1920', None):
                images, warns = self.images_get(product_tmpl_data['image_1920'])
                for warn in warns:
                    all_warns.append((row_index, [warn]))
                image = images and images[0] or None
                product_tmpl_data.update({
                    'image_1920': image,
                })
            else:
                product_tmpl_data.update({
                    'image_1920': None,
                })
            variant_found = False
            route_ids = data.get('route_ids', False)
            if route_ids:
                data['route_ids'] = [(6, 0, route_ids)]
            res_config = self.env['res.config.settings']
            try:
                if res_config.is_import_template_product_variant_logs_active():
                    if log is None:
                        log = self.env['ir.model.log'].create({
                            'name': f'import {wizard.file_filename}',
                            'date_start': date_start,
                            'res_model': 'ir.model.log',
                        })
                        log.attach(wizard.file_filename, wizard.file, mimetype)
                products = self.env['product.product']
                supplier_ids = data.get('seller_ids', False)
                standard_price = data.get('standard_price', 0)
                if tmpls:
                    if (tmpls.company_id
                            and tmpls.company_id != self.env.company):
                        tmpls.company_id = False
                        tmpls = tmpls.sudo(user=self.env.user)
                    tmpls.write(product_tmpl_data)
                    operations.append({'Operation': 'WRITE', 'Object': tmpls,
                                       'Vals': product_tmpl_data})
                    products, variant_found = self.find_products(
                        tmpls, products, attrs.values(), variant_found)
                    if 'product_tmpl_code' in data:
                        del data['product_tmpl_code']
                    if supplier_ids:
                        data['seller_ids'] = self.get_suppliers_data(
                            products, supplier_ids, standard_price)
                    if products:
                        if 'image_variant_1920' in data:
                            images, warns = self.images_get(
                                data['image_variant_1920'])
                            for warn in warns:
                                all_warns.append((row_index, [warn]))
                            data['image_variant_1920'] = (
                                images and images[0] or None)
                        sudo_data = {
                            key: data[key] for key
                            in sudo_keys if products[key].id != data[key]
                        }
                        for key in sudo_keys:
                            del data[key]
                        if 'type' in data:
                            if products.type != data['type']:
                                sudo_data[key] = data['type']
                            del data['type']
                        products.write(data)
                        operations.append({'Operation': 'WRITE',
                                           'Object': products, 'Vals': data})
                        if sudo_data:
                            products = products.sudo().with_company(
                                self.env.company.id
                            ).write(sudo_data)
                            operations.append({'Operation': 'WRITE',
                                               'Object': products,
                                               'Vals': sudo_data})

                    else:
                        attr_values_no_variant, errors = (
                            self.create_attr_or_value(tmpls, attrs))
                        for error in errors:
                            all_errors.append((row_index, [error]))
                        if not errors:
                            tmpls._create_variant_ids()
                            products, variant_found = self.find_products(
                                tmpls, products, attr_values_no_variant,
                                variant_found)
                            if 'image_variant_1920' in data:
                                images, warns = self.images_get(
                                    data['image_variant_1920'])
                                for warn in warns:
                                    all_warns.append((row_index, [warn]))
                                data['image_variant_1920'] = (
                                    images and images[0] or None)
                            products.write(data)
                            operations.append({'Operation': 'WRITE',
                                               'Object': products,
                                               'Vals': data})

                else:
                    if supplier_ids:
                        data['seller_ids'] = self.get_suppliers_data(
                            False, supplier_ids, standard_price)
                    image_variant_1920 = None
                    if 'image_variant_1920' in data:
                        images, warns = self.images_get(
                            data['image_variant_1920'])
                        for warn in warns:
                            all_warns.append((row_index, [warn]))
                        image_variant_1920 = images and images[0] or None
                        del data['image_variant_1920']
                    data.update(product_tmpl_data)
                    tmpls = self.env['product.template'].create(data)
                    operations.append({'Operation': 'CREATE', 'Object': tmpls,
                                       'Vals': data})

                    attr_values_no_variant, errors = (
                        self.with_context(
                            creating_product_tmpl=True
                        ).create_attr_or_value(tmpls, attrs))
                    for error in errors:
                        all_errors.append((row_index, [error]))
                    if not errors:
                        if 'product_tmpl_code' in data:
                            del data['product_tmpl_code']
                        tmpls._create_variant_ids()
                        products, variant_found = self.find_products(
                            tmpls, products, attr_values_no_variant,
                            variant_found)
                        products.write(data)
                        operations.append({
                            'Operation': 'WRITE',
                            'Object': products,
                            'Vals': data,
                        })
                        if image_variant_1920:
                            products.write({
                                'image_variant_1920': image_variant_1920,
                            })
                            operations.append({
                                'Operation': 'WRITE',
                                'Object': products,
                                'Vals': data,
                            })
                if res_config.is_import_template_product_variant_logs_active():
                    description = (
                        self.format_operations_for_description(operations))
                    log.write({
                        'date_finish': fields.Datetime.now(),
                        'description': description,
                    })
                    log.finish(description='')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                savepoint.rollback()
        _add_errors(all_errors)
        _add_warns(all_warns)
        return not orm_errors
