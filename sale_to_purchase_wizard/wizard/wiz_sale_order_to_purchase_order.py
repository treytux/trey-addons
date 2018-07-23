# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _, exceptions


class WizSaleOrderToPurchaseOrder(models.TransientModel):
    _name = 'wiz.sale_order_to_purchase_order'

    @api.model
    def _default_picking_type(self):
        types = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'),
             ('warehouse_id.company_id', '=', self.env.user.company_id.id)])
        if types:
            return types[0].id
        raise exceptions.Warning(
            _('Error!'),
            _('Make sure you have at least an incoming picking type defined'))

    @api.model
    def _default_location_dest_id(self):
        location_id = self.get_default_location_dest_id()
        if location_id:
            return location_id
        main_warehouse = self.env['stock.warehouse'].search([], limit=1)
        if not main_warehouse.exists():
            raise exceptions.Warning(_(
                'At least, you must have created one warehouse.'))
        return (main_warehouse.lot_stock_id and
                main_warehouse.lot_stock_id.id or None)

    @api.onchange('picking_type_id')
    def onchange_picking_type(self):
        self.location_id = self.get_default_location_dest_id()

    @api.multi
    def get_default_location_dest_id(self):
        return (
            self.picking_type_id and
            self.picking_type_id.default_location_dest_id and
            self.picking_type_id.default_location_dest_id.id or None)

    name = fields.Char(
        string='Name')
    product_without_partner_ids = fields.Many2many(
        comodel_name='product.template',
        string='Products without Partner',
        relation='wiz_purchase_order_product_tmpl_rel',
        column1='wiz_purchase_order_id',
        column2='product_tmpl_id')
    stock = fields.Boolean(
        string='Stock',
        default=True,
        help='Check the stock')
    picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Deliver To',
        default=_default_picking_type,
        required=True)
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
        default=_default_location_dest_id)
    wiz_purchase_lines = fields.Many2many(
        comodel_name='wiz.purchase.order.line',
        relation='wiz_purchase_order_sale_or_rel',
        column1='topurchase_order',
        column2='wiz_purchase_order_line')
    stock_type = fields.Selection(
        selection=[('real', ' Manual stock'),
                   ('virtual', 'Virtual stock')],
        string='Stock type',
        default='real',
        help='Generate purchase order lines over selected stock type')

    @api.multi
    def get_products_from_orders(self, orders):
        products = {}
        for order in orders:
            for line in order.order_line:
                pp_state = line.product_id.type in ['service', 'consu']
                pt_state = line.product_id.product_tmpl_id.state in [
                    'end', 'obsolete']
                if not line.product_id or pp_state or pt_state:
                    continue
                product = products.setdefault(
                    line.product_id, dict(product=line.product_id, qty=0))
                product['qty'] += line.product_uom_qty
        if not products:
            raise exceptions.Warning(
                _('No products to create a purchase order'))
        return products

    @api.multi
    def groupby_partner(self, products):
        orderby_partner = {}
        without_partner = []
        self.product_without_partner_ids = [(6, 0, [])]
        for p in products:
            if not products[p]['product']:
                continue
            p_supplier = (p.product_tmpl_id.seller_ids and
                          p.product_tmpl_id.seller_ids[0].name or None)
            p_supplier_id = p_supplier and p_supplier.id or None
            if p_supplier_id is None:
                without_partner.append((0, 0, {
                    'name': p.product_tmpl_id.name,
                    'product_tmpl_id': p.product_tmpl_id.id}))
                continue
            if (p_supplier and
                    not p_supplier.property_product_pricelist_purchase):
                raise exceptions.Warning(_(
                    '%s has not product purchase pricelist assigned. '
                    'Please assing one pricelist') % p_supplier.name)
            if p_supplier_id not in orderby_partner:
                orderby_partner[p_supplier_id] = [products[p]]
            else:
                orderby_partner[p_supplier_id].append(products[p])
        self.product_without_partner_ids = without_partner
        return orderby_partner

    @api.multi
    def create_wiz_purchase_order(self, products_by_partner):
        self.wiz_purchase_lines = [(6, 0, [])]
        wiz_lines = []
        for partner_id in products_by_partner:
            for p in products_by_partner[partner_id]:
                stock_product = p['qty']
                product_qty = None
                if self.stock:
                    stock_product = (self.stock_type == 'real' and
                                     p['product'].qty_available or
                                     p['product'].virtual_available)
                    if p['qty'] >= stock_product:
                        product_qty = p['qty'] - stock_product
                    elif product_qty == 0:
                        continue
                    else:
                        continue
                wiz_lines.append((0, 0, {
                    'product_id': p['product'].id,
                    'date_planned': fields.Date.today(),
                    'partner_id': partner_id,
                    'product_qty': product_qty and product_qty or p['qty']}))
        if not wiz_lines:
            return
        self.wiz_purchase_lines = wiz_lines

    @api.multi
    def button_purchase_view(self):
        orders_ids = self.env.context.get('active_ids', [])
        orders = self.env['sale.order'].browse(orders_ids)
        products = self.get_products_from_orders(orders)
        groupby_partner = self.groupby_partner(products)
        self.create_wiz_purchase_order(groupby_partner)
        res = self.env['ir.model.data'].get_object_reference(
            'sale_to_purchase_wizard', 'purchase_create_ok_wizard')
        return {
            'name': _('Puchase Order lines by partner.'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res and res[1] or False],
            'res_model': 'wiz.sale_order_to_purchase_order',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'partner_list': [p for p in groupby_partner.keys()]},
            'nodestroy': True,
            'target': 'new'}

    @api.multi
    def button_create_purchase(self):
        po_obj = self.env['purchase.order']
        res_partner_obj = self.env['res.partner']
        po_line_obj = self.env['purchase.order.line']
        fiscal_position_obj = self.env['account.fiscal.position']
        purchases_order_ids = []
        partner_list = self.env.context.get('partner_list')
        for partner_id in partner_list:
            partner = res_partner_obj.browse(partner_id)
            pricelist = partner.property_product_pricelist_purchase
            purchase_order = po_obj.create({
                'partner_id': partner_id,
                'currency_id': pricelist.currency_id.id,
                'pricelist_id': pricelist.id,
                'fiscal_position': partner.property_account_position.id,
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.location_id.id,
                'date_order': fields.Date.today(),
                'generate_by_wizard': True})
            partner_products = self.wiz_purchase_lines.filtered(
                lambda x: x.partner_id.id == partner_id)
            for wiz_p_order_line in partner_products:
                product = wiz_p_order_line.product_id
                taxes_ids = product.supplier_taxes_id.filtered(
                    lambda x: x.company_id.id == partner.company_id.id)
                taxes_ids = fiscal_position_obj.map_tax(taxes_ids)
                po_line_obj.create({
                    'order_id': purchase_order.id,
                    'product_id': product.id,
                    'name': wiz_p_order_line.product_id.name,
                    'product_qty': wiz_p_order_line.product_qty,
                    'price_unit': product.standard_price,
                    'state': 'draft',
                    'taxes_id': [(6, 0, [taxes_ids.ids])],
                    'date_planned': fields.Date.today(),
                    'generate_by_wizard': True})
                fiscal_position = purchase_order.fiscal_position.id or False
                po_line_obj.onchange_product_id(
                    pricelist.id,
                    product.id,
                    wiz_p_order_line.product_qty,
                    product.uom_id.id,
                    partner_id,
                    name=wiz_p_order_line.product_id.name,
                    date_planned=fields.Date.today(),
                    fiscal_position_id=fiscal_position,
                    price_unit=product.standard_price,
                    state='draft')
            purchases_order_ids.append(purchase_order.id)
        res = self.env['ir.model.data'].get_object_reference(
            'purchase', 'menu_purchase_rfq')
        data_model = res and res[1] or False
        return {
            'domain': "[('id','in', %s)]" % purchases_order_ids,
            'name': _('Purchase Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': data_model}


class WizPurchaseOrderLine(models.TransientModel):
    _name = 'wiz.purchase.order.line'

    wiz_purchase_id = fields.Many2one(
        comodel_name='wiz.sale_order_to_purchase_order',
        string='Wiz purchase order')
    name = fields.Char(
        string='Name')
    product_uom = fields.Float(
        string='Product Uom')
    product_qty = fields.Float(
        string='Product qty')
    date_planned = fields.Date(
        string='Purchase order date')
    price_unit = fields.Float(
        string='Price Unit')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        domain=[('supplier', '=', True)])
