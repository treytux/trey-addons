###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import calendar

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _purchase_service_generation(self):
        sale_line_purchase_map = {}
        for line in self:
            product = line.product_id
            group_type = product.purchase_service_group_type
            service_to_purchase = product.service_to_purchase
            if not service_to_purchase and line.purchase_line_count == 0:
                continue
            if not group_type:
                result = line._purchase_service_create()
                sale_line_purchase_map.update(result)
            else:
                result = line._purchase_service_group(group_type)
                sale_line_purchase_map.update(result)
        return sale_line_purchase_map

    @api.multi
    def _purchase_service_group(self, group_type='ungrouped'):
        def compute_purchase_date(line=None, supplier=None):
            def _decode_group_days(days_char):
                days_char = days_char.replace(' ', '-').replace(',', '-')
                days_char = [x.strip() for x in days_char.split('-') if x]
                days = [int(x) for x in days_char]
                days.sort()
                return days
            group_day = line.product_id.purchase_group_day
            group_overdue_days = line.product_id.purchase_group_overdue_days
            date_ref = fields.Date.from_string(fields.Date.today())
            date_ref -= relativedelta(days=group_day)
            if group_overdue_days:
                overdue_days = _decode_group_days(group_overdue_days)
                overdue_days.sort()
                days_in_month = calendar.monthrange(
                    date_ref.year, date_ref.month)[1]
                for overdue_day in overdue_days:
                    new_date = None
                    if date_ref.day <= overdue_day:
                        if overdue_day > days_in_month:
                            day = days_in_month
                        date_ref = date_ref + relativedelta(day=day)
                        break
                    if not new_date:
                        day = overdue_days[0]
                        if day > days_in_month:
                            day = days_in_month
                        date_ref = date_ref + relativedelta(day=day, months=1)
            purchase_order = self.env['purchase.order'].search([
                ('partner_id', '=', supplier.id),
                ('state', '=', 'draft'),
                ('company_id', '=', line.company_id.id),
                ('date_order', '=', date_ref)
            ], limit=1)
            if not purchase_order:
                return {'purchase_order': None, 'date_ref': date_ref}
            return {'purchase_order': purchase_order, 'date_ref': date_ref}
        supplier_po_map = {}
        sale_line_purchase_map = {}
        for line in self:
            suppliers = line.product_id.with_context(
                force_company=line.company_id.id)._select_seller(
                quantity=line.product_uom_qty, uom_id=line.product_uom)
            if not suppliers:
                raise UserError(_(
                    'There is no vendor associated to the product %s. Please '
                    'define a vendor for this product.'
                ) % line.product_id.display_name)
            supplier_info = suppliers[0]
            supplier = supplier_info.name
            if group_type == 'ungrouped':
                values = line._purchase_service_prepare_order_values(
                    supplier_info)
                purchase_order = self.env['purchase.order'].create(values)
                supplier_po_map[supplier.id] = purchase_order
            else:
                purchase_data = compute_purchase_date(line, supplier)
                if not purchase_data['purchase_order']:
                    values = super()._purchase_service_prepare_order_values(
                        supplier_info)
                    values['date_order'] = purchase_data['date_ref']
                    purchase_order = self.env['purchase.order'].create(values)
                else:
                    so_name = line.order_id.name
                    origins = []
                    if purchase_order.origin:
                        origins = purchase_order.origin.split(', ') + origins
                    if so_name not in origins:
                        origins += [so_name]
                        purchase_order.write({
                            'origin': ', '.join(origins)
                        })
            values = super()._purchase_service_prepare_line_values(
                purchase_order)
            purchase_line = self.env['purchase.order.line'].create(values)
            sale_line_purchase_map.setdefault(
                line, self.env['purchase.order.line'])
            sale_line_purchase_map[line] |= purchase_line
        return sale_line_purchase_map
