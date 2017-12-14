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
        [[field_onchange.setdefault('variant_line_ids.' + sub, u'') for sub in
         ('product_id', 'disabled', 'value_x', 'value_y', 'product_uom_qty',
          'label_x', 'label_y', 'qty_available')]
         if 'variant_line_ids' in field_onchange else None]
        return super(SaleManageVariant, self).onchange(
            values, field_name, field_onchange)

    @api.multi
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        self.variant_line_ids = [(6, 0, [])]
        template = self.product_tmpl_id
        record = self.env[self.env.context['active_model']].browse(
            self.env.context['active_id'])
        sale_order = record.order_id if self.env.context[
            'active_model'] == 'sale.order.line' else record
        if template and len(template.attribute_line_ids) >= 2:
            lines = []
            for value_x in template.attribute_line_ids[0].value_ids:
                for value_y in template.attribute_line_ids[1].value_ids:
                    product = template.product_variant_ids.filtered(
                        lambda x: (value_x in x.attribute_value_ids and
                                   value_y in x.attribute_value_ids))
                    order_line = sale_order.order_line.filtered(
                        lambda x: x.product_id.id == product.id)
                    lines.append((0, 0, {
                        'product_id': product,
                        'disabled': not bool(product),
                        'value_x': value_x,
                        'value_y': value_y,
                        'product_uom_qty': order_line.product_uom_qty if
                        len(order_line) == 1 else sum(
                            [l.product_uom_qty for l in order_line])}))
                self.variant_line_ids = lines

    @api.multi
    def button_transfer_to_order(self):
        record = self.env[self.env.context['active_model']].browse(
            self.env.context['active_id'])
        sale_order = record.order_id if self.env.context[
            'active_model'] == 'sale.order.line' else record
        lines2unlink = self.env['sale.order.line']
        for line in self.variant_line_ids:
            order_line = sale_order.order_line.filtered(
                lambda x: x.product_id.id == line.product_id.id)
            if order_line:
                if not line.product_uom_qty:
                    lines2unlink |= order_line
                else:
                    if len(order_line) == 1:
                        order_line.product_uom_qty = line.product_uom_qty
                    else:
                        v = sum([l.product_uom_qty for l in order_line])
                        [l_repeat.unlink() for l_repeat in order_line[1:]]
                        order_line.product_uom_qty = v
            elif line.product_uom_qty:
                order_line = self.env['sale.order.line'].create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'order_id': sale_order.id})
                order_line.product_id_change(
                    sale_order.pricelist_id.id, order_line.product_id.id,
                    qty=order_line.product_uom_qty,
                    uom=order_line.product_uom.id,
                    qty_uos=order_line.product_uos_qty,
                    uos=order_line.product_uom.id,
                    partner_id=sale_order.partner_id.id)
        lines2unlink.unlink()


class SaleManageVariantLine(models.TransientModel):
    _name = 'sale.manage.variant.line'

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
        related='value_y.name')
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
