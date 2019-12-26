
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from osv import osv
from osv import fields

class purchase_requisition(osv.osv):
    
    _name = 'purchase.requisition'
    _inherit = 'purchase.requisition'

    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Supplier
        """
        if context is None:
            context = {}
        assert partner_id, 'Supplier should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        delivery_address_id = res_partner.address_get(cr, uid, [supplier.id], ['delivery'])['delivery']
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            if supplier.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                 raise osv.except_osv(_('Warning'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
            location_id = requisition.warehouse_id.lot_input_id.id
            purchase_id = purchase_order.create(cr, uid, {
                        'origin': requisition.name,
                        'partner_id': supplier.id,
                        'partner_address_id': delivery_address_id,
                        'pricelist_id': supplier_pricelist.id,
                        'location_id': location_id,
                        'company_id': requisition.company_id.id,
                        'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                        'requisition_id':requisition.id,
                        'notes':requisition.description,
                        'warehouse_id':requisition.warehouse_id.id ,
            })
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                product = line.product_id
                seller_price, qty, default_uom_po_id, date_planned = self._seller_details(cr, uid, line, supplier, context=context)
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                purchase_order_line.create(cr, uid, {
                    'order_id': purchase_id,
                    'name': product.partner_ref,
                    'product_qty': qty,
                    'product_id': product.id,
                    'product_uom': default_uom_po_id,
                    'price_unit': seller_price,
                    'date_planned': date_planned,
                    'notes': product.description_purchase,
                    'taxes_id': [(6, 0, taxes)],
                    'purchase_requisition_line_id': line.id,   
                }, context=context)
                
        return res
    
    def make_purchase_order_avanzosc(self, cr, uid, ids, context=None):
        """
        Create New RFQ for Supplier
        """
        if context is None:
            context = {}

        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            purchase_order_datas = []
            # Recorro todas las líneas de requisitos
            for line in requisition.line_ids:
                product = line.product_id
                ### SELECCIONO TODOS LOS PROVEEDORES DEL PRODUCTO 
                supplierinfo_obj = self.pool.get('product.supplierinfo')
                supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', product.id)]) 
                if not supplierinfo_ids:
                    # Si no hay proveedores definidos para el producto, muestro el error
                    raise osv.except_osv('Purchase Order Creation Error', 'You must define one supplier for the product: ' + product.name)
                else:
                    for supplierinfo_id in supplierinfo_ids:
                        supplierinfo = supplierinfo_obj.browse(cr, uid, supplierinfo_id)
                        partner = self.pool.get('res.partner')
                        supplier = partner.browse(cr, uid, supplierinfo.name.id)                             
                        ###
                        ### MIRO SI YA EXISTE UN PEDIDO DE COMPRA PARA EL PROVEEDOR QUE VIENE
                        ### DEL PRODUCTO
                        purchase_order_obj = self.pool.get('purchase.order')
                        purchase_order_id = purchase_order_obj.search(cr, uid,[('partner_id', '=', supplier.id),
                                                                               ('state', '=', 'draft'),     
                                                                               ('requisition_id','=', requisition.id)])
                        if not purchase_order_id:
                            # SI NO EXISTE EL PEDIDO DE COMPRA PARA EL CLIENTE
                            delivery_address_id = res_partner.address_get(cr, uid, [supplier.id], ['delivery'])['delivery']
                            supplier_pricelist = supplier.property_product_pricelist_purchase or False
                            
                            
                            location_id = requisition.warehouse_id.lot_input_id.id
                            # Creo purchase order
                            purchase_id = purchase_order.create(cr, uid, {'origin': requisition.name,
                                                                          'partner_id': supplier.id,
                                                                          'partner_address_id': delivery_address_id,
                                                                          'pricelist_id': supplier_pricelist.id,
                                                                          'location_id': location_id,
                                                                          'company_id': requisition.company_id.id,
                                                                          'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                                                                          'requisition_id':requisition.id,
                                                                          'notes':requisition.description,
                                                                          'warehouse_id':requisition.warehouse_id.id ,
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
                        
                        purchase_order_line.create(cr, uid, {'order_id': purchase_id,
                                                             'name': product.partner_ref,
                                                             'product_qty': qty,
                                                             'product_id': product.id,
                                                             'product_uom': default_uom_po_id,
                                                             'price_unit': seller_price,
                                                             'date_planned': date_planned,
                                                             'notes': product.description_purchase,
                                                             'taxes_id': [(6, 0, taxes)],     
                                                             'purchase_requisition_line_id': line.id,                                                      
                                                             }, context=context)                 
                                      
            res[requisition.id] = purchase_order_datas
        
        return True


purchase_requisition()
