##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import datetime, timedelta

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class SaleImportSaleOrderTemplate(models.TransientModel):
    _name = 'sale.import.sale.order.template'
    _description = 'Sale import sale order templates'

    sale_order_template_ids = fields.Many2many(
        comodel_name='sale.order.template',
        relation='sale_import2sale_order_tmpl_rel',
        column1='sale_import_id',
        column2='sale_tmpl_id',
    )
    line_ids = fields.One2many(
        comodel_name='sale.import.sale.order.template.line',
        inverse_name='wizard_id',
        ondelete='cascade',
        string='Wizard lines',
    )
    update_price = fields.Boolean(
        string='Update price unit',
        help='Recompute the price unit with the sale order pricelist',
    )

    @api.multi
    def create_lines(self):
        for wizard in self:
            for sale_order_tmpl in wizard.sale_order_template_ids:
                self.env['sale.import.sale.order.template.line'].create({
                    'wizard_id': wizard.id,
                    'sale_order_template_id': sale_order_tmpl.id,
                })
        view = self.env.ref(
            'sale_order_template_multi_add.view_import_sale_order_templates2')
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context}

    @api.model
    def create_sale_order_lines(self, sale, item):
        sale = sale.with_context(force_set_product_min_qty=True)
        sale_line = self.env['sale.order.line']
        template = item.sale_order_template_id
        for line in template.sale_order_template_line_ids:
            data = sale._compute_line_data_for_template_change(line)
            data.update({
                'order_id': sale.id,
                'product_id': line.product_id.id if line.product_id else False,
                'product_uom_qty': line.product_uom_qty,
            })
            data = sale_line.play_onchanges(data, sale_line._onchange_spec())
            if not self.update_price:
                data.update({
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                })
            data['product_uom_qty'] *= item.qty_factor
            data['price_unit'] *= item.price_unit_factor
            sale_line.create(data)
        sale.sale_order_option_ids = [
            (0, 0, sale._compute_option_data_for_template_change(o))
            for o in template.sale_order_template_option_ids
        ]
        if template.number_of_days > 0:
            sale.validity_date = fields.Date.to_string(
                datetime.now() + timedelta(template.number_of_days))
        sale.require_signature = template.require_signature
        sale.require_payment = template.require_payment
        if template.note:
            sale.note = template.note

    @api.multi
    def select_sale_order_templates(self):
        sale_order_obj = self.env['sale.order']
        for wizard in self:
            sale = sale_order_obj.browse(
                self.env.context.get('active_id', False))
            if sale:
                for item in wizard.line_ids:
                    self.create_sale_order_lines(sale, item)
        return {'type': 'ir.actions.act_window_close'}


class SaleImportProductsLine(models.TransientModel):
    _name = 'sale.import.sale.order.template.line'
    _description = 'Sale import sale order templates lines'

    wizard_id = fields.Many2one(
        comodel_name='sale.import.sale.order.template',
        string='Wizard',
    )
    sale_order_template_id = fields.Many2one(
        comodel_name='sale.order.template',
        string='Sale order template',
    )
    qty_factor = fields.Float(
        string='Quantity factor',
        help='Every line apply the formula: factor * template line quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=1.0,
        required=True,
    )
    price_unit_factor = fields.Float(
        string='Price unit factor',
        help='Every line apply the formula: factor * template line price unit',
        digits=dp.get_precision('Product Unit of Measure'),
        default=1.0,
        required=True,
    )
