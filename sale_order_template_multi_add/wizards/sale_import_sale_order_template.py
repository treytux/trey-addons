##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from datetime import datetime, timedelta

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
        string='Wizard lines',
    )

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
        sale_order_template = item.sale_order_template_id
        for line in sale_order_template.sale_order_template_line_ids:
            values = {
                'order_id': sale.id,
                'product_id': line.product_id.id if line.product_id else False,
                'product_uom_qty': line.product_uom_qty,
                'name': line.name,
                'display_type': line.display_type,
            }
            if not line.display_type:
                price_unit = line.product_id.lst_price
                values.update({
                    'price_unit': price_unit * item.price_unit_factor,
                    'product_uom_qty': line.product_uom_qty * item.qty_factor,
                })
            sale_line.create(values)
        for option in sale.sale_order_option_ids:
            option._compute_discount()
        if sale_order_template.number_of_days > 0:
            sale.validity_date = fields.Date.to_string(
                datetime.now() + timedelta(sale_order_template.number_of_days))
        sale.require_signature = sale_order_template.require_signature
        sale.require_payment = sale_order_template.require_payment
        if sale_order_template.note:
            sale.note = sale_order_template.note

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
        ondelete='cascade',
    )
    sale_order_template_id = fields.Many2one(
        comodel_name='sale.order.template',
        string='Sale order template',
    )
    qty_factor = fields.Float(
        string='Quantity factor',
        help='Every line apply the formula: factor * template line quantity',
        digits='Product Unit of Measure',
        default=1.0,
        required=True,
    )
    price_unit_factor = fields.Float(
        string='Price unit factor',
        help='Every line apply the formula: factor * template line price unit',
        digits='Product Unit of Measure',
        default=1.0,
        required=True,
    )
