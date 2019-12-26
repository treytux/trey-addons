###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class SaleCustomizationAdd(models.TransientModel):
    _name = 'sale.customization.add'
    _description = 'Sale customization add wizard'

    # sale_id = fields.Many2one(
    #     comodel_name='sale.order',
    #     string='Sale')
    # product_tmpl_id = fields.Many2one(
    #     comodel_name='product.template',
    #     string='Product template',
    #     required=True,
    #     domain=[
    #         ('sale_ok', '=', True), '|',
    #         ('attribute_line_ids.value_ids', '!=', False),
    #         ('optional_product_ids', '!=', False)],
    # )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    customization_id = fields.Many2one(
        comodel_name='sale.customization',
        string='Customization')

    @api.multi
    def action_add(self):
        return {
            'type': 'ir.actions.act_window_close',
            'context': {
                'default_product_id': self.product_id.id,
            },
            'infos': {
                'default_product_id': self.product_id.id,
                'default_product_uom_qty': 1,
                'default_customization_id': self.customization_id.id
            }
        }
