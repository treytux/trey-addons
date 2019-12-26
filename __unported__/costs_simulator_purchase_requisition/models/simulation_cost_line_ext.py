
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

class simulation_cost_line(osv.osv):

    _name = 'simulation.cost.line'
    _inherit = 'simulation.cost.line'
    
    _columns = {# Campo para saber con que Solicitud de Compra esta relacionada la simulacion
                'purchase_requisition_ids':fields.one2many('purchase.requisition.line','simulation_cost_line_id','Purchase Requisition Line'), 
                # Campo para saber con que Pedido de Compra esta relacionada la linea de simulación de costes
                'purchase_order_id':fields.many2one('purchase.order', 'Purchase Order', readonly=True),
                # Campo para saber con que Linea de Pedido de Compra esta relacionada la linea de simulación de costes
                'purchase_order_line_id':fields.many2one('purchase.order.line', 'Purchase Order Line', readonly=True),
        }


simulation_cost_line()
