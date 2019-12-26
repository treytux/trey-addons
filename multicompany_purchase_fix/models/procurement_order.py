# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        return super(ProcurementOrder, self.with_context(
            company_id=self.company_id.id)).make_po()

    @api.model
    def _calc_new_qty_price(self, procurement, po_line=None, cancel=False):
        if 'company_id' not in self.env.context:
            return super(ProcurementOrder, self)._calc_new_qty_price(
                procurement, po_line, cancel)
        if not po_line:
            po_line = procurement.purchase_line_id
        qty = self.env['product.uom']._compute_qty(
            procurement.product_uom.id, procurement.product_qty,
            procurement.product_id.uom_po_id.id)
        if cancel:
            qty = -qty
        supplierinfo_min_qty = 0.0
        if po_line.order_id.location_id.usage != 'customer':
            if (
                    po_line.product_id.seller_id.id ==
                    po_line.order_id.partner_id.id):
                supplierinfo_min_qty = po_line.product_id.seller_qty
            else:
                supplierinfos = self.env['product.supplierinfo'].search([
                    ('name', '=', po_line.order_id.partner_id.id),
                    ('product_tmpl_id', '=',
                        po_line.product_id.product_tmpl_id.id),
                    ('company_id', '=', procurement.company_id.id),
                ])
                if not supplierinfos:
                    supplierinfos = self.env['product.supplierinfo'].search([
                        ('name', '=', po_line.order_id.partner_id.id),
                        ('product_tmpl_id', '=',
                            po_line.product_id.product_tmpl_id.id),
                        ('company_id', '=', None),
                    ])
                supplierinfo_min_qty = (
                    supplierinfos and supplierinfos[0].min_qty or
                    supplierinfo_min_qty)
        if supplierinfo_min_qty == 0.0:
            qty += po_line.product_qty
        else:
            for proc in po_line.procurement_ids:
                qty += self.env['product.uom']._compute_qty(
                    proc.product_uom.id, proc.product_qty,
                    proc.product_id.uom_po_id.id) if (
                    proc.state == 'running') else 0.0
            qty = max(qty, supplierinfo_min_qty) if qty > 0.0 else 0.0
        price = po_line.price_unit
        if qty != po_line.product_qty:
            supplier = po_line.order_id.partner_id
            pricelist = supplier.property_product_pricelist_purchase
            price = pricelist.with_context(
                uom=procurement.product_id.uom_po_id.id).price_get(
                    procurement.product_id.id, qty,
                    po_line.order_id.partner_id.id)[pricelist.id]
        return qty, price

    @api.model
    def _get_product_supplier(self, procurement):
        if 'company_id' not in self.env.context:
            return super(ProcurementOrder, self)._get_product_supplier(
                procurement)
        company_suppliers = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=',
                procurement.product_id.product_tmpl_id.id),
            ('company_id', '=', procurement.company_id.id),
        ], order='sequence')
        if not company_suppliers:
            company_suppliers = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=',
                    procurement.product_id.product_tmpl_id.id),
                ('company_id', '=', None),
            ], order='sequence')
        if company_suppliers:
            return company_suppliers[0].name
        return procurement.product_id.seller_id
