# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        ede_procurement = []
        for procurement in self:
            route = procurement.route_ids and procurement.route_ids[0]
            company = self.env.user.company_id
            supplier = self.with_context(
                force_company=company.id)._get_product_supplier(procurement)
            if supplier != company.ede_supplier_id:
                return super(ProcurementOrder, self).make_po()
            if not route.is_sale_one_purchase and not route.is_drop_shipping:
                return super(ProcurementOrder, self).make_po()
            ede_procurement.append(procurement)
        res = procurement.make_po_ede(ede_procurement)
        return res

    @api.multi
    def make_po_ede(self, ede_procurement):
        res = {}
        company = self.env.user.company_id
        purchases = []
        for procurement in ede_procurement:
            ctx = self.env.context.copy()
            ctx['force_company'] = company.id
            schedule_date = self._get_purchase_schedule_date(
                procurement, company)
            supplier = self.env['procurement.order'].with_context(
                ctx)._get_product_supplier(self)
            line_values = self.env['procurement.order'].with_context(
                ctx)._get_po_line_values_from_proc(
                procurement, supplier, company, schedule_date)
            origin = procurement.origin.split(':')[0]
            route = procurement.route_ids and procurement.route_ids[0]
            sale_order = self.env['sale.order'].search([('name', '=', origin)])
            ede_order_reference =\
                sale_order.client_order_ref or sale_order.name
            sale_order_line = self.env['sale.order.line'].search([
                ('order_id', '=', sale_order.id),
                ('product_id', '=', procurement.product_id.id),
                ('route_id', '=', route.id)])
            if sale_order_line.is_ede_danger:
                line_values['is_ede_danger'] = True
            if route.is_drop_shipping:
                customer_shipping_id = sale_order.partner_shipping_id.id,
                draft_orders = self.env['purchase.order'].search([
                    ('partner_id', '=', supplier.id), ('state', '=', 'draft'),
                    ('company_id', '=', procurement.company_id.id),
                    ('origin', 'like', origin),
                    ('ede_client_order_ref', '=', ede_order_reference),
                    ('customer_shipping_id', '=', customer_shipping_id),
                    ('is_ede_custom', '=', True),
                ])
            else:
                draft_orders = self.env['purchase.order'].search([
                    ('partner_id', '=', supplier.id), ('state', '=', 'draft'),
                    ('company_id', '=', procurement.company_id.id),
                    ('origin', 'like', origin),
                    ('is_ede_custom', '=', True),
                ])
            if draft_orders:
                order_id = draft_orders and draft_orders[0].id
                line_values['order_id'] = order_id
                self.env['purchase.order.line'].create(line_values)
                msg = _("Draft Purchase Order update")
            else:
                order_values = procurement.generate_order_values()
                if route.is_drop_shipping:
                    order_values['customer_shipping_id'] = \
                        sale_order.partner_shipping_id.id
                order_values['ede_client_order_ref'] = ede_order_reference
                order_id = self.env['procurement.order'].sudo().with_context(
                    ctx).create_procurement_purchase_order(
                    procurement, order_values, line_values)
                msg = _("Draft Purchase Order create")
            order = self.env['purchase.order'].browse([order_id])
            res[procurement.id] = order.order_line and order.order_line[0].id
            procurement.purchase_line_id = \
                order.order_line and order.order_line[0].id
            order.message_post(msg)
            purchases.append(order)
        for purchase in purchases:
            if not purchase.order_line:
                purchase.unlink()
            lines_danger = purchase.mapped('order_line').filtered(
                lambda l: l.is_ede_danger is True)
            if not lines_danger:
                continue
            purchase_copy = purchase.copy()
            lines_normal = purchase_copy.mapped('order_line').filtered(
                lambda l: l.is_ede_danger is False)
            purchase_copy.origin = purchase.origin
            purchase.is_ede_danger = True
            lines_danger.unlink()
            lines_normal.unlink()
        return res

    @api.model
    def generate_order_values(self):
        name = self.env['ir.sequence'].get(
            'purchase.order') or _('PO: %s') % self.name
        company = self.env.user.company_id
        supplier = self.env['procurement.order'].with_context(
            force_company=company.id)._get_product_supplier(self)
        schedule_date = self.env[
            'procurement.order']._get_purchase_schedule_date(self, company)
        purchase_date = self.env['procurement.order']._get_purchase_order_date(
            self, company, schedule_date)
        p_type = company.ede_picking_type_id
        order_values = {
            'name': name,
            'origin': self.origin,
            'partner_id': supplier.id,
            'picking_type_id': p_type.id or None,
            'location_id': p_type.default_location_dest_id.id,
            'pricelist_id':
                supplier.property_product_pricelist_purchase.id,
            'currency_id':
                supplier.property_product_pricelist_purchase and
                supplier.property_product_pricelist_purchase.currency_id.id or
                self.company_id.currency_id.id,
            'date_order': purchase_date.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT),
            'company_id': self.company_id.id,
            'fiscal_position': self.env['purchase.order'].with_context(
                force_company=supplier.id).onchange_partner_id(
                supplier.id)['value']['fiscal_position'],
            'payment_term_id':
                supplier.property_supplier_payment_term.id or False,
            'dest_address_id': False,
            'is_ede_custom': True,
            'adarra_ede_state': 'draft',
        }
        return order_values
