##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta


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
        order_lines = []
        if item.sale_order_template_id.title:
            order_lines.append((0, 0, {
                'name': item.sale_order_template_id.title,
                'display_type': 'line_section',
            }))
        if item.sale_order_template_id.header_note:
            order_lines.append((0, 0, {
                'name': item.sale_order_template_id.header_note,
                'display_type': 'line_note',
            }))
        template = item.sale_order_template_id
        for line in template.sale_order_template_line_ids:
            data = sale._compute_line_data_for_template_change(line)
            if not line.product_id:
                order_lines.append((0, 0, data))
                continue
            discount = 0
            pricelist = sale.pricelist_id.with_context(
                uom=line.product_uom_id.id)
            if pricelist:
                price = pricelist.get_product_price(line.product_id, 1, False)
                if pricelist.discount_policy == 'without_discount' and \
                   line.price_unit:
                    discount = (
                        (line.price_unit - price) / line.price_unit * 100)
                    if discount < 0:
                        discount = 0
                    else:
                        price = line.price_unit
            else:
                price = line.price_unit
            data.update({
                'price_unit': price,
                'discount': (
                    100 - ((100 - discount) * (100 - line.discount) / 100)),
                'product_uom_qty': line.product_uom_qty,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom_id.id,
                'customer_lead': sale._get_customer_lead(
                    line.product_id.product_tmpl_id),
            })
            if pricelist:
                data.update(self.env['sale.order.line']._get_purchase_price(
                    pricelist,
                    line.product_id,
                    line.product_uom_id,
                    fields.Date.context_today(sale)))
            order_lines.append((0, 0, data))
        sale.order_line = order_lines
        sale.order_line._compute_tax_id()
        option_lines = []
        for option in template.sale_order_template_option_ids:
            data = sale._compute_option_data_for_template_change(option)
            option_lines.append((0, 0, data))
        sale.sale_order_option_ids = option_lines
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
    quantity = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=1.0,
        required=True,
    )
