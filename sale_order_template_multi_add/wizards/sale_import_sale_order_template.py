##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


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
        if item.sale_order_template_id.title:
            sale_line = self.env['sale.order.line'].create({
                'order_id': sale.id,
                'name': item.sale_order_template_id.title,
                'display_type': 'line_section',
            })
        if item.sale_order_template_id.header_note:
            sale_line = self.env['sale.order.line'].create({
                'order_id': sale.id,
                'name': item.sale_order_template_id.header_note,
                'display_type': 'line_note',
            })
        sale_order_tmpl = item.sale_order_template_id
        for so_tmpl_line in sale_order_tmpl.sale_order_template_line_ids:
            sale_line = self.env['sale.order.line'].create({
                'order_id': sale.id,
                'name': so_tmpl_line.product_id.name,
                'product_id': so_tmpl_line.product_id.id,
                'product_uom_qty': (
                    so_tmpl_line.product_uom_qty * item.quantity),
                'product_uom': so_tmpl_line.product_id.uom_id.id,
                'price_unit': (
                    so_tmpl_line.price_unit or
                    so_tmpl_line.product_id.list_price),
            })
            sale_line.product_id_change()
        for so_option_line in sale_order_tmpl.sale_order_template_option_ids:
            sale_order_option = self.env['sale.order.option'].create({
                'order_id': sale.id,
                'name': so_option_line.product_id.name,
                'product_id': so_option_line.product_id.id,
                'quantity': so_option_line.quantity * item.quantity,
                'uom_id': so_option_line.product_id.uom_id.id,
                'price_unit': (
                    so_option_line.price_unit or
                    so_option_line.product_id.list_price),
                'discount': so_option_line.discount,
            })
            sale_order_option._onchange_product_id()

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
