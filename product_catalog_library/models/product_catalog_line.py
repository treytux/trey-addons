###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductCatalogLine(models.Model):
    _name = 'product.catalog.line'
    _description = 'Product catalog line'
    _order = 'line_num, id'

    line_num = fields.Integer(
        string='Excel line',
        required=True,
        index=True,
    )
    default_code = fields.Char(
        string='Default code',
        index=True,
    )
    product_code = fields.Char(
        string='Product code',
        index=True,
    )
    ean = fields.Char(
        string='EAN',
        index=True,
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    supplier_ref = fields.Char(
        string='Supplier reference',
    )
    product_tmpl_code = fields.Char(
        string='Template code',
        index=True,
    )
    source_data = fields.Json(
        string='Imported values',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('error', 'Error'),
        ],
        string='Status',
        default='pending',
        required=True,
        index=True,
    )
    error_message = fields.Text(
        string='Error',
    )

    @api.model
    def _normalise(self, value):
        if value in (None, False):
            return ''
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()

    @api.model
    def _product_code(self, values):
        code = self._normalise(values.get('product_code'))
        if code:
            return code
        return '%s%s' % (
            self._normalise(values.get('supplier_ref')),
            self._normalise(values.get('default_code')))

    @api.model
    def _find_product(self, ean, product_code):
        product_obj = self.env['product.product'].with_context(
            active_test=False)
        if ean:
            product = product_obj.search([
                ('barcode', '=', ean)
            ], limit=1)
            if product:
                return product
        if product_code:
            return product_obj.search([
                ('default_code', '=', product_code),
            ], limit=1)
        return product_obj

    @api.model
    def _attribute_lines(self, rows):
        attributes = {}
        for row in rows:
            for key, value in row.items():
                if not key.startswith('attribute:') or not value:
                    continue
                attr_name = key.split(':', 1)[1].strip()
                values = [item.strip() for item in str(value).split(',')]
                attributes.setdefault(attr_name, set()).update(values)
        result = []
        attribute_obj = self.env['product.attribute']
        for attr_name, value_names in attributes.items():
            attribute = attribute_obj.search([
                ('name', '=', attr_name),
            ], limit=1)
            if not attribute:
                attribute = attribute_obj.create({
                    'name': attr_name,
                })
            value_ids = []
            for value_name in sorted(value_names):
                value = attribute.value_ids.filtered(
                    lambda item: item.name == value_name)
                if not value:
                    value = self.env['product.attribute.value'].create({
                        'name': value_name,
                        'attribute_id': attribute.id,
                    })
                value_ids.append(value.id)
            result.append((0, 0, {
                'attribute_id': attribute.id,
                'value_ids': [(6, 0, value_ids)],
            }))
        return result

    @api.model
    def _template_values(self, row, attribute_lines):
        values = {
            'name': self._normalise(row.get('name')),
            'type': self._normalise(row.get('type')) or 'consu',
            'categ_id': self.env.ref('product.product_category_all').id,
            'attribute_line_ids': attribute_lines,
        }
        for field_name in (
                'sale_ok', 'purchase_ok', 'list_price', 'invoice_policy',
                'description_sale', 'description_purchase', 'weight'):
            if field_name in row and row[field_name] not in (None, ''):
                values[field_name] = row[field_name]
        return values

    def _variant_for_row(self, template, row):
        values = []
        for key, value in row.items():
            if key.startswith('attribute:') and value:
                values.append(self._normalise(value).split(',')[0].strip())
        if not values and len(template.product_variant_ids) == 1:
            return template.product_variant_id
        for product in template.product_variant_ids:
            attribute_values = product.product_template_attribute_value_ids
            product_values = attribute_values.mapped('name')
            if sorted(product_values) == sorted(values):
                return product
        return template.product_variant_id

    def _update_template_attributes(self, template, rows):
        for row in rows:
            for key, value in row.items():
                if not key.startswith('attribute:') or not value:
                    continue
                attribute = self.env['product.attribute'].search([
                    ('name', '=', key.split(':', 1)[1].strip())
                ], limit=1)
                if not attribute:
                    attribute = self.env['product.attribute'].create({
                        'name': key.split(':', 1)[1].strip(),
                    })
                line = template.attribute_line_ids.filtered(
                    lambda item: item.attribute_id == attribute)
                value_names = [
                    item.strip() for item in str(value).split(',')]
                for value_name in value_names:
                    attr_value = attribute.value_ids.filtered(
                        lambda item: item.name == value_name)
                    if not attr_value:
                        attr_value = self.env[
                            'product.attribute.value'].create({
                                'name': value_name,
                                'attribute_id': attribute.id,
                            })
                    if line:
                        line.write({
                            'value_ids': [(4, attr_value.id)],
                        })
                    else:
                        template.attribute_line_ids.create({
                            'product_tmpl_id': template.id,
                            'attribute_id': attribute.id,
                            'value_ids': [(4, attr_value.id)],
                        })

    def _apply_product_values(self, product, row):
        values = {}
        for field_name in product._fields:
            if field_name in row and field_name not in (
                    'id', 'product_tmpl_id', 'default_code', 'barcode'):
                field = product._fields[field_name]
                if field.type in (
                        'char', 'text', 'float', 'integer', 'boolean',
                        'selection'):
                    values[field_name] = row[field_name]
        values['default_code'] = (
            row.get('product_code') or row.get('default_code') or '')
        if row.get('ean'):
            values['barcode'] = row['ean']
        if values:
            product.write(values)

    def action_activate(self):
        for line in self:
            try:
                line._activate()
            except UserError as error:
                line.write({
                    'state': 'error',
                    'error_message': str(error),
                })
        return True

    def _activate(self):
        self.ensure_one()
        if self.product_tmpl_code:
            rows = self.search([
                ('product_tmpl_code', '=', self.product_tmpl_code),
            ])
        else:
            rows = self
        product = self._find_product(self.ean, self.product_code)
        template = product.product_tmpl_id if product else self.product_tmpl_id
        data = self.source_data or {}
        row_values = json.loads(data) if isinstance(data, str) else data
        group_rows = []
        for row in rows:
            row_data = row.source_data or {}
            group_rows.append(
                json.loads(row_data) if isinstance(row_data, str) else row_data)
        if not template:
            template = self.env['product.template'].create(
                self._template_values(
                    row_values, self._attribute_lines(group_rows)))
        else:
            self._update_template_attributes(template, group_rows)
        template.active = True
        template._create_variant_ids()
        for row in rows:
            row_data = row.source_data or {}
            row_data = (
                json.loads(row_data)
                if isinstance(row_data, str)
                else row_data)
            variant = row._variant_for_row(template, row_data)
            variant.active = True
            row._apply_product_values(variant, row_data)
            row.write({
                'product_tmpl_id': template.id,
                'product_id': variant.id,
                'state': 'active',
                'error_message': False,
            })
        return template

    @api.model
    def create_from_row(self, values):
        values = dict(values)
        source_data = values.get('source_data') or dict(values)
        values['default_code'] = self._normalise(values.get('default_code'))
        values['ean'] = self._normalise(values.get('ean'))
        values['product_code'] = self._product_code(values)
        values['name'] = self._normalise(values.get('name')) or values[
            'product_code']
        values['source_data'] = source_data
        line_values = {
            key: value for key, value in values.items()
            if key in self._fields
        }
        return self.create(line_values)
