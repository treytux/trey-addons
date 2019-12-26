# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp

### Heredo esta clase para añadirle un nuevo botón, este botón no solicitará
### un proveedor en concreto, sino que dará de alta tantos presupuestos, como
### proveedores distintos tenga el producto.
class PurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _inherit = 'purchase.requisition'
 
    @api.multi
    def make_purchase_order(self, partner_id):
        """
        Create New RFQ for Supplier
        """
        purchase_order = self.env['purchase.order']
        purchase_order_line = self.env['purchase.order.line']
        res_partner = self.env['res.partner']
        fiscal_position = self.env['account.fiscal.position']
        res = {}
        for requisition in self:
            purchase_order_datas = []
            # Recorro todas las líneas de requisitos
            for line in requisition.line_ids:
                product = line.product_id
                ### SELECCIONO TODOS LOS PROVEEDORES DEL PRODUCTO 
                supplierinfo_obj = self.pool.get('product.supplierinfo')
                supplierinfo_ids = supplierinfo_obj.search([('product_id','=', product.product_tmpl_id.id)])
                if not supplierinfo_ids:
                    # Si no hay proveedores definidos para el producto, muestro el error
                    raise exceptions.Warning(
                        _('Purchase Order Creation Error'),
                        _('You must define one supplier for the product: '
                          '%s')) % product.name
                else:
                    for supplierinfo_id in supplierinfo_ids:
                        supplierinfo = supplierinfo_obj.browse(supplierinfo_id)
                        partner = self.pool.get('res.partner')
                        supplier = partner.browse(supplierinfo.name.id)
                        ### MIRO SI YA EXISTE UN PEDIDO DE COMPRA PARA EL PROVEEDOR QUE VIENE
                        ### DEL PRODUCTO
                        purchase_order_obj = self.pool.get('purchase.order')
                        purchase_order_id = purchase_order_obj.search([
                            ('partner_id', '=', supplier.id),
                            ('state', '=', 'draft'),
                            ('requisition_id','=', requisition.id)])
                        if not purchase_order_id:
                            # SI NO EXISTE EL PEDIDO DE COMPRA PARA EL CLIENTE
                            delivery_address_id = res_partner.address_get(
                                [supplier.id], ['delivery'])['delivery']
                            supplier_pricelist = supplier.property_product_pricelist_purchase or False
                            location_id = requisition.warehouse_id.lot_input_id.id
                            # Creo purchase order
                            purchase_id = purchase_order.create({
                                'origin': requisition.name,
                                'partner_id': supplier.id,
                                'partner_address_id': delivery_address_id,
                                'pricelist_id': supplier_pricelist.id,
                                'location_id': location_id,
                                'company_id': requisition.company_id.id,
                                'fiscal_position':
                                   supplier.property_account_position and supplier.property_account_position.id or False,
                                'requisition_id':requisition.id,
                                'notes':requisition.description,
                                'warehouse_id':requisition.warehouse_id.id
                            })
                            purchase_order_datas.append(purchase_id)
                        else:
                            # SI EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR
                            # Cojo el ID del pedido de compra
                            purchase_id = purchase_order_id[0]
                        # DOY DE ALTA LA LINEA DEL PEDIDO DE COMPRA
                        delivery_address_id = res_partner.address_get(cr, uid, [supplier.id], ['delivery'])['delivery']
                        supplier_pricelist = supplier.property_product_pricelist_purchase or False                                            
                        seller_price, qty, default_uom_po_id, date_planned = self._seller_details(cr, uid, line, supplier, context=context)
                        taxes_ids = product.supplier_taxes_id
                        taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)                        
                        purchase_order_line.create({
                            'order_id': purchase_id,
                            'name': product.partner_ref,
                            'product_qty': qty,
                            'product_id': product.id,
                            'product_uom': default_uom_po_id,
                            'price_unit': seller_price,
                            'date_planned': date_planned,
                            'notes': product.description_purchase,
                            'taxes_id': [(6, 0, taxes)]
                        })
            res[requisition.id] = purchase_order_datas
        return True
