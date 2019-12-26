
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

class purchase_order_line(osv.osv):

    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'
    
    _columns = {# Campo para saber con que linea de solicitudes de compra esta asociada la linea del pedido de compra
                'purchase_requisition_line_id':fields.many2one('purchase.requisition.line', 'Purchase Requisition Line'),
                # Campo para saber que línea de simulación de coste esta relacionada la linea de pedido de compra
                'simulation_cost_line_ids':fields.one2many('simulation.cost.line','purchase_order_line_id','Simulation Cost Lines'), 
        }
    
    def action_confirm(self, cr, uid, ids, context=None):
        
        purchase_requisition_line_obj = self.pool.get('purchase.requisition.line')
        simulation_cost_line_obj = self.pool.get('simulation.cost.line')
        
        # Trato las lineas de Pedido de Compra
        for purchase_line_id in ids:
            purchase_line = self.browse(cr, uid, purchase_line_id)
            # Si la linea del pedido de compra, esta asociada a una linea de solicitud de compra
            if purchase_line.purchase_requisition_line_id:
                purchase_requisition_line = purchase_requisition_line_obj.browse(cr, uid, purchase_line.purchase_requisition_line_id.id)
                # Si la linea de solicitud de compra, ya tiene asociada un ID de un Pedido de Compra, es un error
                if purchase_requisition_line.purchase_order_id:
                    #
                    ### Es un error porque se esta confirmando una linea de pedido de compra, que esta asignada a una linea de
                    ### solicitud de compra, que ya tiene asignada otro linea de pedido de compra.
                    raise osv.except_osv('Purchase Order Error', purchase_line.product_id.name + ' product already confirmed in another purchase order')
                else:
                    # Modifico la Fecha Planifica de la linea del Pedido de Compra, con la fecha Estimada de Compra de la linea de simulacion de costes.
                    self.write(cr,uid,[purchase_line.id],{'date_planned': purchase_requisition_line.simulation_cost_line_id.estimated_date_purchase_completion}) 
                    # Modifico la línea de solicitud de compra, con el ID de la Orden de Compra
                    purchase_requisition_line_obj.write(cr,uid,[purchase_requisition_line.id],{'purchase_order_id': purchase_line.order_id.id}) 
                    # Modifico la linea de simulacion de coste, con el proveedor, y el precio de coste del producto, y el pedido de compra
                    simulation_cost_line_obj.write(cr,uid,[purchase_requisition_line.simulation_cost_line_id.id],{'supplier_id':  purchase_line.order_id.partner_id.id,
                                                                                                                  'purchase_price': purchase_line.price_unit,
                                                                                                                  'purchase_order_id': purchase_line.order_id.id,
                                                                                                                  'purchase_order_line_id': purchase_line.id})  

                    
        
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)
        return True


purchase_order_line()
