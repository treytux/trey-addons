###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_not_increases_maintenance_price = fields.Boolean(
        string='Not increase maintenance price?',
        help='Indicates that the line product does not affect the associated '
             'maintenance product.',
    )
    is_maintenance_line = fields.Boolean(
        string='Maintenance line?',
        help='Internal field to indicate that the line is the maintenance '
             'product.',
    )
    is_maintenance_section = fields.Boolean(
        string='Maintenance section?',
        help='Internal field to indicate that the line is the maintenance '
             'section.',
    )
    linked_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Linked Order Line',
        ondelete='cascade',
    )

    @api.constrains('is_maintenance_line')
    def _check_is_maintenance_line_unique(self):
        maintenance_lines = self.order_id.order_line.filtered(
            lambda ln: ln.is_maintenance_line)
        if len(maintenance_lines) > 1:
            raise ValidationError(_(
                'Only one maintenance line can exist on a sales order.'))

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        self.is_not_increases_maintenance_price = not bool(
            self.product_id.product_tmpl_id.maintenance_percentage > 0)
        return res

    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product = self.env['product.product'].browse(
                vals.get('product_id'))
            vals['is_not_increases_maintenance_price'] = not bool(
                product.maintenance_percentage > 0)
        res = super().create(vals)
        if self._context.get('no_add_maintenance_line'):
            return res
        res.order_id.create_or_update_maintenance_line()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if self._context.get('no_add_maintenance_line'):
            return res
        if self._context.get('force_update_maintenance_line'):
            self.mapped('order_id').create_or_update_maintenance_line()
            return res
        if True in self.mapped('is_maintenance_line'):
            raise UserError(_(
                'It is not allowed to modify a maintenance line. The values ​​'
                'of this line are calculated automatically.'))
        self.mapped('order_id').create_or_update_maintenance_line()
        return res

    @api.multi
    def unlink(self):
        if not self.exists():
            return True
        sales = self.mapped('order_id')
        res = super().unlink()
        if self._context.get('no_add_maintenance_line'):
            return res
        for sale in sales:
            if not sale.order_line:
                return res
            sale.create_or_update_maintenance_line()
        return res
