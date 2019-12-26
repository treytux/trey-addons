
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

#
class sale_order(osv.osv):
    
    _name = 'sale.order'
    _inherit = 'sale.order'

    #
    ### FUNCION QUE SE EJECUTA CUANDO CONFIRMO UN PEDIDO DE VENTA
    
    def action_wait(self, cr, uid, ids, context=None):
        
        sale_order_obj = self.pool.get('sale.order')
        simulation_template_obj = self.pool.get('simulation.template')
        coste_line_obj = self.pool.get('simulation.cost.line')
        
        ### Accedo al PEDIDO DE VENTA
        sale_order2 = sale_order_obj.browse(cr, uid, ids[0])   

        #
        ### SI EL PEDIDO DE VENTA VIENE DE UNA SIMULACION, COJO LA ÚLTIMA SIMULACIÓN
        ### ACTIVA QUE NO ESTE CANCELADA, O LA ÚLTIMA HITORIFICADA
        w_found = 0
        w_simulation_cost_id = 0
        w_maxid = 0
        if sale_order2.simulation_cost_ids:
            ### Recorro todas las simulaciones asociadas al pedido de venta
            for simulation_cost in  sale_order2.simulation_cost_ids:
                if (not simulation_cost.historical_ok) and (simulation_cost.state not in ('canceled')):
                    # Si es una simulación activa, me quedo con este id
                    w_found = 1
                    w_simulation_cost_id = simulation_cost.id
                else:
                    # Si no ha encontrado la activa me quedo con la última 
                    # simulación de coste historificada (la mas nueva, la de mayor id)
                    if w_found == 0:
                        if simulation_cost.id > w_maxid:
                            w_maxid = simulation_cost.id

            if w_simulation_cost_id == 0:
                # Si no he encontrado una simulación de coste activa para ese pedido de venta
                if w_maxid == 0:
                    # Si no he encontrado una simulación de coste historificada para ese pedido de venta
                    raise osv.except_osv('Project Creation Error', 'Simulation Cost not found')
                else:
                    #Si no he encontrado una simulación de coste activa para ese pedido de venta,
                    # me quedo con el id de la simulación de coste historificada mas nueva
                    w_simulation_cost_id = w_maxid

        #
        ### Si EL PEDIDO DE VENTA VIENE DE UNA SIMULACIÓN, MIRO SI YA TIENE ASOCIADO
        ### UN PROYECTO
        if sale_order2.simulation_cost_ids:
            if not sale_order2.project2_id:
                #SI EL PEDIDO DE VENTA NO TIENE UN PROYECTO ASOCIADO, LO CREO
                #
                ## Cojo el nombre de la simulacion
                simulation_cost_obj = self.pool.get('simulation.cost') 
                simulation_cost = simulation_cost_obj.browse(cr, uid, w_simulation_cost_id)
                ## primero creo la cuenta analítica
                line = {'name' : 'PROJ ' + simulation_cost.simulation_number + ' / ' + sale_order2.name,
                        'type': 'view',
                        'state': 'open',
                        'estimated_balance': 0,
                        'estimated_cost': 0,
                        'estimated_sale': 0,
                        }
                #
                # DOY DE ALTA LA CUENTA ANALITICA
                #
                account_analytic_account_obj = self.pool.get('account.analytic.account')
                account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)
                w_cuenta_analitica = account_analytic_account_id
                # 
                # DOY DE ALTA EL PROYECTO
                #
                line = {'name' : 'PROJ ' + simulation_cost.simulation_number + ' / ' + sale_order2.name,
                        'analytic_account_id': w_cuenta_analitica,
                        }
                project_project_obj = self.pool.get('project.project')
                project_project_id = project_project_obj.create(cr, uid, line)
                # Modifico el pedido de venta con el id del proyecto creado
                sale_order_obj2 = self.pool.get('sale.order') 
                sale_order_obj2.write(cr,uid,[sale_order2.id],{'project2_id': project_project_id})       
                
                #
                ### CREO UNA SUBCUENTA ANALITICA POR CADA PESTAÑA DEL SIMULADOR DE COSTES,
                ### Y TAMBIEN CREO UN SUBPROYECTO PARA LAS PESTAÑA "INTERNAL TASK"
                simulation_cost_line_obj = self.pool.get('simulation.cost.line')
                simulation_cost_line_ids = simulation_cost_line_obj.search(cr, uid,[('simulation_cost_id','=', simulation_cost.id)])
                for simulation_cost_line_id in simulation_cost_line_ids:
                    simulation_cost_line = simulation_cost_line_obj.browse(cr, uid, simulation_cost_line_id)   
                    #
                    ### CASO 1: Si la linea viene de una plantilla de simulacion normal
                    #
                    if simulation_cost_line.template_id and simulation_cost_line.template_type == 'N':

                        if simulation_cost_line.sale_order_line_id.order_id.id == sale_order2.id:
                             
                            simulation_template = simulation_template_obj.browse(cr, uid, simulation_cost_line.template_id.id)
                            w_literal = 'SUBP ' + simulation_cost.simulation_number + ' / ' + simulation_template.name + ' / ' + sale_order2.name
                            sub_account_analytic_account_obj = self.pool.get('account.analytic.account')
                            sub_account_analytic_account_ids = sub_account_analytic_account_obj.search(cr, uid,[('name','=', w_literal)])
                            if not sub_account_analytic_account_ids:
                                ## primero creo la Subcuenta analítica
                                line = {'name' : w_literal,
                                        'parent_id':  w_cuenta_analitica,
                                        'type': 'normal',
                                        'state': 'open',
                                        'estimated_balance': 0,
                                        'estimated_cost': 0,
                                        'estimated_sale': 0,
                                        }
                                ## doy de alta la subcuenta analítica
                                account_analytic_account_obj = self.pool.get('account.analytic.account')
                                w_sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)                          
                                #
                                ### creo la subcuenta analitica para la pestaña compras (purchases)
                                w_literal2 = w_literal + ' (Purchase)'
                                line = {'name' : w_literal2,
                                        'parent_id':  w_sub_account_analytic_account_id,
                                        'type': 'normal',
                                        'state': 'open',
                                        'estimated_balance': 0,
                                        'estimated_cost': 0,
                                        'estimated_sale': 0,
                                        }
                                account_analytic_account_obj = self.pool.get('account.analytic.account')
                                sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)       
                                #
                                ### creo la subcuenta analitica para la pestaña investment
                                w_literal2 = w_literal + ' (Investment)'
                                line = {'name' : w_literal2,
                                        'parent_id':  w_sub_account_analytic_account_id,
                                        'type': 'normal',
                                        'state': 'open',
                                        'estimated_balance': 0,
                                        'estimated_cost': 0,
                                        'estimated_sale': 0,
                                        }
                                account_analytic_account_obj = self.pool.get('account.analytic.account')
                                sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)                          
                                #
                                ### creo la subcuenta analítica para la pestaña subcontracting
                                w_literal2 = w_literal + ' (Subcontracting Services)'
                                line = {'name' : w_literal2,
                                        'parent_id':  w_sub_account_analytic_account_id,
                                        'type': 'normal',
                                        'state': 'open',
                                        'estimated_balance': 0,
                                        'estimated_cost': 0,
                                        'estimated_sale': 0,
                                        }
                                account_analytic_account_obj = self.pool.get('account.analytic.account')
                                sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)                
                                #
                                ### creo la subcuenta analitica para la pestaña others
                                w_literal2 = w_literal + ' (Others)'
                                line = {'name' : w_literal2,
                                        'parent_id':  w_sub_account_analytic_account_id,
                                        'type': 'normal',
                                        'state': 'open',
                                        'estimated_balance': 0,
                                        'estimated_cost': 0,
                                        'estimated_sale': 0,
                                        }
                                account_analytic_account_obj = self.pool.get('account.analytic.account')
                                sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)      
                                #
                                ### creo la subcuenta analitica para la pestaña internal task
                                w_literal2 = w_literal + ' (Internal Task)'
                                line = {'name' : w_literal2,
                                        'parent_id':  w_sub_account_analytic_account_id,
                                        'type': 'normal',
                                        'state': 'open',
                                        'estimated_balance': 0,
                                        'estimated_cost': 0,
                                        'estimated_sale': 0,
                                        }
                                account_analytic_account_obj = self.pool.get('account.analytic.account')
                                sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)
                                # ahora creo el subproyecto
                                line = {'name' : w_literal2,
                                        'analytic_account_id': sub_account_analytic_account_id,
                                }          
                                project_project_obj = self.pool.get('project.project')
                                w_project_subproject_id = project_project_obj.create(cr, uid, line)         
                                
            else:
                w_cuenta_analitica = sale_order2.project2_id.analytic_account_id.id

                
        #
        ### SI EL PEDIDO DE VENTA VIENE DE UNA SIMULACION
        if sale_order2.simulation_cost_ids:                     
            #
            ### Trato las lineas de PURCHASE 
            for coste_line_id in simulation_cost.purchase_cost_lines_ids:
                coste_line = coste_line_obj.browse(cr, uid, coste_line_id.id) 
                if coste_line.purchase_order_id:
                    # Solo tengo que imputar los costes
                    self._imputar_en_analitica(cr, uid, sale_order2, coste_line, w_cuenta_analitica)
            #
            ### Trato las lineas de INVESTMENT
            for coste_line_id in simulation_cost.investment_cost_lines_ids:
                coste_line = coste_line_obj.browse(cr, uid, coste_line_id.id) 
                if coste_line.purchase_order_id:
                    # Solo tengo que imputar los costes
                    self._imputar_en_analitica(cr, uid, sale_order2, coste_line, w_cuenta_analitica)
            #
            ### Trato las lineas de SUBCONTRACTING    
            for coste_line_id in simulation_cost.subcontracting_cost_lines_ids:
                coste_line = coste_line_obj.browse(cr, uid, coste_line_id.id) 
                if coste_line.purchase_order_id:
                    # Solo tengo que imputar los costes
                    self._imputar_en_analitica(cr, uid, sale_order2, coste_line, w_cuenta_analitica)
            #
            ### Trato las lineas de OTHERS
            for coste_line_id in simulation_cost.others_cost_lines_ids:                
                coste_line = coste_line_obj.browse(cr, uid, coste_line_id.id) 
                if coste_line.product_id.type != 'service' or (coste_line.product_id.type == 'service' and coste_line.product_id.procure_method != 'make_to_stock' and coste_line.product_id.supply_method == 'buy'): 
                    if coste_line.purchase_order_id:
                        # Solo tengo que imputar los costes
                        self._imputar_en_analitica(cr, uid, sale_order2, coste_line, w_cuenta_analitica)
                
                        
        super(sale_order,self).action_wait(cr, uid, ids, context)
        
        return True  

    #
    ### FUNCION PARA IMPUTAR COSTES EN CUENTAS ANALITICAS    

    def _imputar_en_analitica(self, cr, uid, sale_order2, coste_line, w_cuenta_analitica):
           
        account_analytic_account_obj = self.pool.get('account.analytic.account')
        sub_account_analytic_account_obj = self.pool.get('account.analytic.account')
        simulation_cost_obj = self.pool.get('simulation.cost') 
        simulation_template_obj = self.pool.get('simulation.template') 
        purchase_order_obj = self.pool.get('purchase.order')
        purchase_order_line_obj = self.pool.get('purchase.order.line')
           
        # MODIFICACION DE LA CUENTA ANALÍTICA (DEL PROYECTO)
    
        account_analytic_account = account_analytic_account_obj.browse(cr, uid, w_cuenta_analitica)
        w_estimated_cost = account_analytic_account.estimated_cost
        w_estimated_cost = w_estimated_cost + coste_line.subtotal_purchase
        w_estimated_sale = account_analytic_account.estimated_sale
        w_estimated_sale = w_estimated_sale + coste_line.subtotal_sale
        w_estimated_balance = w_estimated_sale - w_estimated_cost
        account_analytic_account_obj.write(cr, uid, [w_cuenta_analitica], {'estimated_cost': w_estimated_cost,
                                                                           'estimated_sale': w_estimated_sale,
                                                                           'estimated_balance': w_estimated_balance})
           
        #
        ### Voy a generar el literal a buscar en subcuenta analítica
        w_literal = ''
        #
        # Cojo el nombre de la simulacion de costes
        simulation_cost = simulation_cost_obj.browse(cr, uid, coste_line.simulation_cost_id.id)
           
        if not coste_line.template_id:
            # Si no viene de una plantilla de simulacion
            w_literal = 'SUBP ' + simulation_cost.simulation_number + ' / NO FROM Simulation Template / ' + sale_order2.name
        else:
            # Si viene de una plantilla de simulacion    
            simulation_template = simulation_template_obj.browse(cr, uid, coste_line.template_id.id)
            # Genero el literal a buscar
            w_literal = 'SUBP ' + simulation_cost.simulation_number + ' / ' + simulation_template.name + ' / ' + sale_order2.name
            
        #
        # CON EL LITERAL GENERADO, BUSCO LA SUBCUENTA ANALÍTICA PARA VER
        # SI EXISTE O NO    
        sub_account_analytic_account_ids = sub_account_analytic_account_obj.search(cr, uid,[('name','=', w_literal)])
        # En este punto debería o no de haber encontrado 1 sola subcuenta analítica
        w_found = 0
        for sub_account_analytic_account in sub_account_analytic_account_ids:
            # Si existe la subcuenta analítica, cojo su ID
            w_found = 1
            sub_account_analytic_account_id = sub_account_analytic_account
                               
        # Si no encuentro el subproyecto, lo creo
        if w_found == 0:
            if coste_line.template_id:
                raise osv.except_osv('Purchase Order Creation Error(from sale order)', 'Subaccount analytic account not found, literal: ' + w_literal)
            else:
                line = {'name' : w_literal,
                        'parent_id':  w_cuenta_analitica,
                        'type': 'normal',
                        'state': 'open',
                        'estimated_balance': 0,
                        'estimated_cost': 0,
                        'estimated_sale': 0,
                        }

                account_analytic_account_obj = self.pool.get('account.analytic.account')
                sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)           
              
        # MODIFICACION DE LA SUBCUENTA ANALÍTICA (DEL SUBPROYECTO)
        sub_account_analytic_account = sub_account_analytic_account_obj.browse(cr, uid, sub_account_analytic_account_id)
        w_estimated_cost = sub_account_analytic_account.estimated_cost
        w_estimated_cost = w_estimated_cost + coste_line.subtotal_purchase
        w_estimated_sale = sub_account_analytic_account.estimated_sale
        w_estimated_sale = w_estimated_sale + coste_line.subtotal_sale
        w_estimated_balance = w_estimated_sale - w_estimated_cost
        sub_account_analytic_account_obj.write(cr, uid, [sub_account_analytic_account_id], {'estimated_cost': w_estimated_cost,
                                                                                            'estimated_sale': w_estimated_sale,
                                                                                            'estimated_balance': w_estimated_balance})           
    
        # Genero el literal para buscar las subcuenta analitica de la pentaña de la que vengo
        w_text = coste_line.type_cost
        w_literal2 = w_literal + ' (' + w_text + ')'
        sub_account_analytic_account_ids = sub_account_analytic_account_obj.search(cr, uid,[('name','=', w_literal2),
                                                                                            ('parent_id','=', sub_account_analytic_account_id)])
           
        if sub_account_analytic_account_ids:
            # Si ha encontrado alguna linea, solo habrá encontrado 1,
            # ya que esta buscado una cuenta en concreto, así que me 
            # quedo con su ID
            sub_account_analytic_account_id2 = sub_account_analytic_account_ids[0]
        else:
            if w_type == 3:
                raise osv.except_osv('Purchase Order Creation Error', 'Subaccount Analytic for tab not found(1), literal: ' + w_literal2)
            else:
                line = {'name' : w_literal2,
                        'parent_id':  sub_account_analytic_account_id,
                        'type': 'normal',
                        'state': 'open',
                        'estimated_balance': 0,
                        'estimated_cost': 0,
                        'estimated_sale': 0,
                        }
                sub_account_analytic_account_id2 = account_analytic_account_obj.create(cr, uid, line)
     
        # UNA VEZ LLEGADO A ESTE PUNTO, YA PUEDO HACER LA IMPUTACION DE LAS ESTIMACIONES
        # A LA SUBCUENTA ANALITICA PERTENECIENTE A LA PESTAÑA DE LA SIMULACION DE COSTES
        sub_account_analytic_account = sub_account_analytic_account_obj.browse(cr, uid, sub_account_analytic_account_id2)
        w_estimated_cost = sub_account_analytic_account.estimated_cost
        w_estimated_cost = w_estimated_cost + coste_line.subtotal_purchase
        w_estimated_sale = sub_account_analytic_account.estimated_sale
        w_estimated_sale = w_estimated_sale + coste_line.subtotal_sale
        w_estimated_balance = w_estimated_sale - w_estimated_cost
        sub_account_analytic_account_obj.write(cr, uid, [sub_account_analytic_account_id2], {'estimated_cost': w_estimated_cost,                                                                                        
                                                                                             'estimated_sale': w_estimated_sale,
                                                                                             'estimated_balance': w_estimated_balance}) 
        #
        ### Actualizo la linea del pedido de compra con la subcuenta analitica
        purchase_order_line_obj.write(cr,uid,[coste_line.purchase_order_line_id.id],{'account_analytic_id': sub_account_analytic_account_id2}) 
        #
        ### Actualizo el Pedido de Compra con el ID del Pedido de Venta, y con el ID del proyecto
        purchase_order_obj.write(cr,uid,[coste_line.purchase_order_id.id],{'sale_order_id': sale_order2.id,
                                                                           'project2_id': sale_order2.project2_id.id,}) 
                                                                                        
                    
        return True
    
sale_order()
