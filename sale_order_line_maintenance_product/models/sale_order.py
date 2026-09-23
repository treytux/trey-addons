###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    maintenance_active = fields.Boolean(
        string='Sale order maintenance active?',
        compute='_compute_maintenance_active',
    )

    def _compute_maintenance_active(self):
        for sale in self:
            if all([
                    ln.is_not_increases_maintenance_price
                    for ln in sale.order_line]):
                sale.maintenance_active = False
            else:
                sale.maintenance_active = True

    @api.depends('order_line', 'order_line.is_not_increases_maintenance_price')
    def create_or_update_maintenance_line(self):
        if not self:
            return False
        self.ensure_one()
        if not self.company_id.maintenance_product_tmpl_id.product_variant_id:
            return False
        if len(self.order_line) == 1 and self.order_line.is_maintenance_line:
            self.order_line.unlink()
            return False
        maintenance_product = (
            self.company_id.maintenance_product_tmpl_id.product_variant_id)
        sequence = self.order_line and self.order_line[-1].sequence + 1 or 99999
        maintenance_data = {
            'order_id': self.id,
            'is_maintenance_line': True,
            'sequence': sequence + 1,
            'product_id': maintenance_product.id,
            'product_uom_qty': 1,
            'name': self.get_maintenance_name(
                self.order_line, maintenance_product),
            'price_unit': self.get_maintenance_price(self.order_line),
        }
        maintenance_line = self.order_line.filtered(
            lambda ln: ln.is_maintenance_line).with_context(
            no_add_maintenance_line=True)
        if maintenance_line:
            maintenance_line.write(maintenance_data)
        else:
            maintenance_line = maintenance_line.create(maintenance_data)
        section_vals = {
            'order_id': self.id,
            'linked_line_id': maintenance_line.id,
            'display_type': 'line_section',
            'is_not_increases_maintenance_price': True,
            'is_maintenance_section': True,
            'sequence': sequence,
            'name': _('Maintenance'),
        }
        section_lines = self.order_line.filtered(
            lambda ln: ln.is_maintenance_section
            or ln.linked_line_id == maintenance_line
        ).with_context(no_add_maintenance_line=True)
        if section_lines:
            if len(section_lines) > 1:
                section_lines = section_lines.sorted(
                    key=lambda ln: ln.id, reverse=True)
                section_lines[1:].unlink()
            section_lines[0].write(section_vals)
        else:
            section_lines.create(section_vals)
        return True

    def get_maintenance_price(self, sale_lines_maintenance):
        self.ensure_one()
        price = sum([
            line.price_subtotal
            * line.product_id.product_tmpl_id.maintenance_percentage / 100
            for line in sale_lines_maintenance
            if not line.is_not_increases_maintenance_price
        ])
        if price <= 0:
            return price
        if price < self.company_id.maintenance_product_tmpl_id.list_price:
            price = self.company_id.maintenance_product_tmpl_id.list_price
        return price

    def get_maintenance_name(
            self, sale_lines_maintenance, maintenance_product):
        maintenance_name = '%s\n' % maintenance_product.display_name
        components_name = ''
        for ln in sale_lines_maintenance:
            components_name += '\n'
            if ln.is_not_increases_maintenance_price or not ln.product_id:
                continue
            if ln.is_maintenance_line:
                continue
            components_name = '\t%s %s x %s\n' % (
                ln.product_uom_qty, ln.product_uom.name,
                ln.product_id.default_code)
            maintenance_name += components_name
        return maintenance_name

    def copy_data(self, default=None):
        self.ensure_one()
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            if 'order_line' in vals:
                for count, order_line_vals in enumerate(vals['order_line']):
                    if order_line_vals[2].get('is_maintenance_line'):
                        del vals['order_line'][count]
        return vals_list
