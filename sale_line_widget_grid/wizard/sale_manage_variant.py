# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.decimal_precision as dp
from openerp import api, models, fields


class SaleManageVariant(models.TransientModel):
    _name = 'sale.manage.variant'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Template',
        required=True)
    variant_line_ids = fields.Many2many(
        comodel_name='sale.manage.variant.line',
        relation='sale_variant_variant_line_rel',
        column1='sale_variant',
        column2='sale_variant_line')

    @api.multi
    def onchange(self, values, field_name, field_onchange):
        fields = ('product_id', 'disabled', 'value_x', 'value_y',
                  'product_uom_qty', 'label_x', 'label_y', 'qty_available')
        [[field_onchange.setdefault('variant_line_ids.' + sub, u'') for sub in
         fields] if 'variant_line_ids' in field_onchange else None]
        return super(SaleManageVariant, self).onchange(
            values, field_name, field_onchange)

    @api.multi
    def get_attribute_in_order(self, attrs):
        return ([att for att in attrs if att.attribute_id.type != 'color'][0],
                [att for att in attrs if att.attribute_id.type == 'color'][0])

    @api.multi
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        def _get_sale_order(context):
            record = self.env[self.env.context['active_model']].browse(
                self.env.context['active_id'])
            sale_order = record.order_id if self.env.context[
                'active_model'] == 'sale.order.line' else record
            return sale_order

        template = self.product_tmpl_id
        if not template or len(template.attribute_line_ids.ids) > 2:
            return
        self.variant_line_ids = [(6, 0, [])]
        sale_order = _get_sale_order(self.env.context)
        lines = []
        attribute_1, attribute_2 = self.get_attribute_in_order(
            template.attribute_line_ids)
        y_dict_values = (len(template.attribute_line_ids) == 2 and
                         attribute_2.value_ids or template)
        for value_x in attribute_1.value_ids:
            for value_y in y_dict_values:
                if len(template.attribute_line_ids) == 1:
                    product = template.product_variant_ids.filtered(
                        lambda x: (value_x in x.attribute_value_ids))
                    value_y = product.attribute_value_ids[0].attribute_id.id
                else:
                    product = template.product_variant_ids.filtered(
                        lambda x: (value_x in x.attribute_value_ids and
                                   value_y in x.attribute_value_ids))
                order_line = sale_order.order_line.filtered(
                    lambda x: x.product_id.id == product.id)
                no_limit = product.product_tmpl_id.no_stock_limit
                lines.append((0, 0, {
                    'product_id': product,
                    'disabled': True if no_limit else False,
                    'value_x': value_x,
                    'value_y': value_y,
                    'product_uom_qty': order_line.product_uom_qty if
                    len(order_line) == 1 else sum(
                        l.product_uom_qty for l in order_line)}))
            self.variant_line_ids = lines

    @api.multi
    def button_transfer_to_order(self):
        model = self.env.context['active_model']
        record = self.env[model].browse(self.env.context['active_id'])
        sale_order = record.order_id if model == 'sale.order.line' else record
        lines2unlink = sale_order_line = self.env['sale.order.line']
        lines = sale_order.order_line
        for line in self.variant_line_ids:
            order_line = lines.filtered(
                lambda x: x.product_id.id == line.product_id.id)
            if order_line:
                if not line.product_uom_qty:
                    lines2unlink |= order_line
                else:
                    if len(order_line) == 1:
                        res = order_line.product_id_change(
                            sale_order.pricelist_id.id,
                            line.product_id.id,
                            qty=line.product_uom_qty,
                            partner_id=sale_order.partner_id.id)
                        order_line.product_uom_qty = line.product_uom_qty
                        order_line.write(res['value'])
                    else:
                        v = sum(l.product_uom_qty for l in order_line)
                        [l_repeat.unlink() for l_repeat in order_line[1:]]
                        order_line.product_uom_qty = v
            elif line.product_uom_qty:
                order_line = sale_order_line.create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'order_id': sale_order.id})
        lines2unlink and lines2unlink.unlink()


class SaleManageVariantLine(models.TransientModel):
    _name = 'sale.manage.variant.line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Variant',
        readonly=True)
    disabled = fields.Float(
        string='Disabled',
        compute='_compute_stock')
    value_x = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Value x')
    label_x = fields.Char(
        string='X',
        related='value_x.name')
    value_y = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Value y')
    label_y = fields.Char(
        string='Y',
        compute='_compute_label')
    product_uom_qty = fields.Float(
        digits_compute=dp.get_precision('Product UoS'),
        string='Quantity')
    qty_available = fields.Float(
        string='Quantity On Hand',
        related='product_id.qty_available')
    available_block = fields.Float(
        string='Disable input without product stock',
        default=0)
    available_label = fields.Char(string='Stock: ')

    @api.one
    @api.depends('product_id')
    def _compute_label(self):
        attrs = self.product_id.product_tmpl_id.attribute_line_ids
        self.label_y = (
            len(attrs) == 1 and
            attrs[0].attribute_id.name or self.value_y.name)

    @api.one
    @api.depends('product_id')
    def _compute_stock(self):
        no_limit_stock = self.product_id.product_tmpl_id.no_stock_limit
        self.disabled = 1 if no_limit_stock else 0
