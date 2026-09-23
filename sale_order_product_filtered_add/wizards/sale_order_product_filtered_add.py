##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import fields, models


class SaleOrderProductFilteredAdd(models.TransientModel):
    _name = 'sale.order.product.filtered.add'
    _description = 'Product Filtered Add'

    state = fields.Selection(
        string='State',
        selection=[
            ('step_1', 'Filtering'),
            ('step_2', 'Selecting'),
        ],
        required=True,
        default='step_1',
    )
    product_category_ids = fields.Many2many(
        string='Product Categories',
        comodel_name='product.category',
        relation='product_filtered_categ_rel',
        column1='wizard_product_filtered_id',
        column2='product_category_id',
        help='Filter by product internal category',
    )
    product_feature_value_ids = fields.Many2many(
        string='Product Feature Values',
        comodel_name='product.feature.value',
        relation='product_filtered_feature_value_rel',
        column1='wizard_product_filtered_id',
        column2='product_feature_value_id',
        help='Filter by product feature value',
    )
    product_filtered_ids = fields.Many2many(
        string='Filtered Products',
        comodel_name='product.product',
        relation='wizard_product_filtered2product_filter_rel',
        column1='wizard_product_filtered_id',
        column2='product_id',
    )
    product_selected_ids = fields.Many2many(
        string='Selected Products',
        comodel_name='product.product',
        relation='wizard_product_filtered2product_select_rel',
        column1='wizard_product_selected_id',
        column2='product_id',
    )

    def _get_filter_domain(self):
        domain = []
        if self.product_category_ids:
            domain.append((
                'categ_id', 'child_of', self.product_category_ids.ids))
        if self.product_feature_value_ids:
            domain.append(
                ('feature_line_ids.value_ids',
                    'in',
                    self.product_feature_value_ids.ids))
        return domain

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {
                'order_id': self._context['active_id'],
            }}

    def _create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        data = record._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        new._origin = record
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
                new.update(data)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def action_step_filter(self):
        products = self.env['product.product'].search(
            self._get_filter_domain())
        self.product_filtered_ids = [(6, 0, products.ids)]
        self.state = 'step_2'
        return self._reopen_view()

    def action_step_select(self):
        self.ensure_one()
        sale_id = self._context['order_id']
        sale_line_obj = self.env['sale.order.line']
        for line in self.product_selected_ids:
            data = {}
            data.update({
                'order_id': sale_id,
                'product_id': line.id,
                'product_uom_qty': 1.00,
            })
            self._create_with_onchange(sale_line_obj, data)
