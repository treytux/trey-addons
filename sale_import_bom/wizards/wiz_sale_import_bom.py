###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class WizSaleImportBom(models.TransientModel):
    _name = 'wiz.sale_import_bom'
    _description = 'Import BoM to a sale order'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order',
        required=True,
        ondelete='cascade',
    )
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='BoM',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
    )
    only_import_products = fields.Boolean(
        string='Only import products',
        help='Only import the components without adding the main product',
    )

    def _prepare_sale_order_line_values(self, product, qty):
        return {
            'order_id': self.order_id.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
        }

    def button_add(self):
        self.ensure_one()
        sol_obj = self.env['sale.order.line']
        main_product = (
            self.bom_id.product_id
            or self.bom_id.product_tmpl_id.product_variant_ids[:1]
        )
        if not main_product and not self.only_import_products:
            msg = _('The bill of materials does not have a valid variant.')
            raise UserError(msg)
        if not self.only_import_products:
            vals = self._prepare_sale_order_line_values(
                main_product, self.quantity)
            vals['price_unit'] = 0.0
            sol_obj.create(vals)
        for line in self.bom_id.bom_line_ids:
            if not line.product_id:
                continue
            vals = self._prepare_sale_order_line_values(
                line.product_id, self.quantity * line.product_qty)
            sol_obj.create(vals)
        return {'type': 'ir.actions.act_window_close'}
