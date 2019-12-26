
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

class simulation_cost(osv.osv):

    _name = 'simulation.cost'
    _inherit = 'simulation.cost'
    
    _columns = {# Campo para saber con que Solicitud de Compra esta relacionada la simulacion
                'purchase_requisition_id':fields.many2one('purchase.requisition', 'Purchase Requisition')
        }
    #
    ### BOTÓN para crear la solicitud de compra
    def button_create_purchase_requistion(self, cr, uid, ids, *args):
        
        purchase_requisition_obj = self.pool.get('purchase.requisition')
        purchase_requisition_line_obj = self.pool.get('purchase.requisition.line')
        #
        ### Leo el Objeto Coste
        simulation_cost = self.browse(cr, uid, ids[0])
        #
        ### Creo el objeto PURCHASE.REQUISITION
        values_line = {'name': simulation_cost.name,
                       'exclusive': 'multiple',      
                       }
        purchase_requisition_id = purchase_requisition_obj.create(cr, uid, values_line) 
        #
        ### T R A T O   L I N E A S   "PURCHASE"
        for cost_line_id in simulation_cost.purchase_cost_lines_ids:
            values_line = {'requisition_id': purchase_requisition_id,
                           'product_id': cost_line_id.product_id.id,
                           'product_qty': cost_line_id.amount,   
                           'product_uom_id': cost_line_id.uom_id.id,   
                           'simulation_cost_line_id': cost_line_id.id,
                           }
            purchase_requisition_line_obj.create(cr, uid, values_line)
        #
        ### T R A T O   L I N E A S   "INVESTMENT" 
        for cost_line_id in simulation_cost.investment_cost_lines_ids:
            values_line = {'requisition_id': purchase_requisition_id,
                           'product_id': cost_line_id.product_id.id,
                           'product_qty': cost_line_id.amount,   
                           'product_uom_id': cost_line_id.uom_id.id,   
                           'simulation_cost_line_id': cost_line_id.id,
                           }
            purchase_requisition_line_obj.create(cr, uid, values_line)
        #
        ### T R A T O   L I N E A S   "SUBCONTRACTING"
        for cost_line_id in simulation_cost.subcontracting_cost_lines_ids:
            values_line = {'requisition_id': purchase_requisition_id,
                           'product_id': cost_line_id.product_id.id,
                           'product_qty': cost_line_id.amount,   
                           'product_uom_id': cost_line_id.uom_id.id,   
                           'simulation_cost_line_id': cost_line_id.id,
                           }
            purchase_requisition_line_obj.create(cr, uid, values_line)
        #
        ### T R A T O   L I N E A S   "OTHERS"
        for cost_line_id in simulation_cost.others_cost_lines_ids:
            if cost_line_id.product_id.type != 'service' or (cost_line_id.product_id.type == 'service' and cost_line_id.product_id.procure_method != 'make_to_stock' and cost_line_id.product_id.supply_method == 'buy'): 
                values_line = {'requisition_id': purchase_requisition_id,
                               'product_id': cost_line_id.product_id.id,
                               'product_qty': cost_line_id.amount,   
                               'product_uom_id': cost_line_id.uom_id.id,   
                               'simulation_cost_line_id': cost_line_id.id,
                               }
                purchase_requisition_line_obj.create(cr, uid, values_line)
            
        #
        ### Actualizo la simulación con el ID de la Solicitud de compra creada
        self.write(cr,uid,ids[0],{'purchase_requisition_id': purchase_requisition_id}) 
 

        return True 

simulation_cost()
