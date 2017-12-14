# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.decimal_precision as dp
from openerp import api, models, fields


class PurchaseManageVariant(models.TransientModel):
    _name = 'purchase.manage.variant'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Template',
        required=True)
    variant_line_ids = fields.Many2many(
        comodel_name='purchase.manage.variant.line',
        relation='purchase_variant_variant_line_rel',
        column1='purchase_variant',
        column2='purchase_variant_line')

    @api.multi
    def onchange(self, values, field_name, field_onchange):
        fields = ('product_id', 'disabled', 'value_x', 'value_y',
                  'product_qty', 'label_x', 'label_y')
        [[field_onchange.setdefault('variant_line_ids.' + sub, u'') for sub in
         fields] if 'variant_line_ids' in field_onchange else None]
        return super(PurchaseManageVariant, self).onchange(
            values, field_name, field_onchange)

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        template = self.product_tmpl_id
        if not template or len(template.attribute_line_ids.ids) > 2:
            return
        self.variant_line_ids = [(6, 0, [])]
        model = self.env.context['active_model']
        record = self.env[model].browse(self.env.context['active_id'])
        purchase_order = (
            record.order_id if model == 'purchase.order.line' else record)
        lines = []
        y_dict_value = template
        if len(template.attribute_line_ids) == 2:
            y_dict_value = template.attribute_line_ids[1].value_ids
        for value_x in template.attribute_line_ids[0].value_ids:
            for value_y in y_dict_value:
                if len(template.attribute_line_ids) == 1:
                    product = template.product_variant_ids.filtered(
                        lambda x: (value_x in x.attribute_value_ids))
                    value_y = (
                        product.attribute_value_ids[0].attribute_id)
                else:
                    product = template.product_variant_ids.filtered(
                        lambda x: (value_x in x.attribute_value_ids and
                                   value_y in x.attribute_value_ids))
                order_line = purchase_order.order_line.filtered(
                    lambda x: x.product_id.id == product.id)
                lines.append((0, 0, {
                    'product_id': product,
                    'disabled': not bool(product),
                    'value_x': value_x.id,
                    'value_y': value_y.id,
                    'product_qty': order_line.product_qty if
                    len(order_line) == 1 else sum(
                        l.product_qty for l in order_line)}))
        self.variant_line_ids = lines

    @api.multi
    def button_transfer_to_order(self):
        model = self.env.context['active_model']
        record = self.env[model].browse(self.env.context['active_id'])
        purchase_order = (
            record.order_id if model == 'purchase.order.line' else record)
        lines2unlink = purchase_lines = self.env['purchase.order.line']
        lines = purchase_order.order_line
        for line in self.variant_line_ids:
            order_line = lines.filtered(
                lambda x: x.product_id.id == line.product_id.id)
            if order_line:
                if not line.product_qty:
                    lines2unlink |= order_line
                else:
                    if len(order_line) == 1:
                        order_line.product_qty = line.product_qty
                    else:
                        v = sum(l.product_qty for l in order_line)
                        [l_repeat.unlink() for l_repeat in order_line[1:]]
                        order_line[0].product_qty = v
            elif line.product_qty:
                order_line = purchase_lines.create({
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'order_id': purchase_order.id,
                    'price_unit': line.product_id.standard_price,
                    'product_qty': line.product_qty,
                    'date_planned': purchase_order.date_order})
                order_line.onchange_product_id(
                    purchase_order.pricelist_id.id,
                    line.product_id.id,
                    line.product_qty,
                    order_line.product_uom.id,
                    purchase_order.partner_id.id)
        lines2unlink and lines2unlink.unlink()


class PurchaseManageVariantLine(models.TransientModel):
    _name = 'purchase.manage.variant.line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Variant',
        readonly=True)
    disabled = fields.Boolean(
        string='Disabled')
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
    product_qty = fields.Float(
        digits_compute=dp.get_precision('Product UoS'),
        string='Quantity')

    @api.one
    @api.depends('product_id')
    def _compute_label(self):
        attrs = self.product_id.product_tmpl_id.attribute_line_ids
        self.label_y = (len(attrs) == 1 and
                        attrs[0].attribute_id.name or self.value_y.name)
