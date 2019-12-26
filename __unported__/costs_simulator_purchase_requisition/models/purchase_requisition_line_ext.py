
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

class purchase_requisition_line(osv.osv):

    _name = 'purchase.requisition.line'
    _inherit = 'purchase.requisition.line'
    
    _columns = {# Campo para saber con que linea de la simulacion de costes esta asociada la linea de la solicitud de compra
                'simulation_cost_line_id':fields.many2one('simulation.cost.line', 'Simulation Cost Line'),
                # Campo para saber con que Linea de Pedido de Compra esta relacionada la linea de la Solicitud de Compra
                'purchase_order_line_ids':fields.one2many('purchase.order.line','purchase_requisition_line_id','Purchase Order Line'), 
                # Campo para saber con que Pedido de Compra esta relacionada la linea de solicitud de compra.
                'purchase_order_id':fields.many2one('purchase.order', 'Purchase Order'),
        }


purchase_requisition_line()
