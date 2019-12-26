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
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

#
### HEREDO ESTA CLASE PARA MODIFICAR EL TRATAMIENTO DE CREAR PROYECTOS,
### Y SUS TAREAS, CUANDO EL PEDIDO DE VENTA HA SIDO GENERADO DESDE
### UNA SIMULACIÓN DE COSTE
#
class procurement_order(osv.osv):
    _name = 'procurement.order'
    _inherit = "procurement.order"

    def action_produce_assign_service(self, cr, uid, ids, context=None):  

        project_task = self.pool.get('project.task')
        partner_obj = self.pool.get('res.partner')
        warehouse_obj = self.pool.get('stock.warehouse')
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        w_simulation_cost_id2 = 0
        for procurement in self.browse(cr, uid, ids, context=context):
            project = self._get_project(cr, uid, procurement, context=context)
            planned_hours = self._convert_qty_company_hours(cr, uid, procurement, context=context)
            #
            ### Accedo a la LINEA DEL PEDIDO DE VENTA
            sale_order_line_obj = self.pool.get('sale.order.line') 
            sale_order_line = sale_order_line_obj.browse(cr, uid, procurement.sale_line_id.id)
            #
            ### Accedo al PEDIDO DE VENTA
            sale_order_obj = self.pool.get('sale.order') 
            sale_order = sale_order_obj.browse(cr, uid, sale_order_line.order_id.id)
            #
            ### SI EL PEDIDO DE VENTA VIENE DE UNA SIMULACION, COJO LA ÚLTIMA SIMULACIÓN
            ### ACTIVA QUE NO ESTE CANCELADA, O LA ÚLTIMA HITORIFICADA
            w_found = 0
            w_simulation_cost_id = 0
            w_maxid = 0
            if sale_order.simulation_cost_ids:
                ### Recorro todas las simulaciones asociadas al pedido de venta
                for simulation_cost in  sale_order.simulation_cost_ids:
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
            if sale_order.simulation_cost_ids:
                if not sale_order.project2_id:
                    raise osv.except_osv('Purchase Order Creation Error', 'Project not found')
                else:                    
                    #SI EL PEDIDO DE VENTA TIENE UN PROYECTO ASOCIADO, COJO SU ID 
                    project_project_id = sale_order.project2_id.id
                    # Ahora cojo su cuenta analítica
                    project_project_obj = self.pool.get('project.project') 
                    project_project = project_project_obj.browse(cr, uid,  project_project_id)
                    account_analytic_account_id = project_project.analytic_account_id.id              
                                          
            #
            ### SI EL PEDIDO DE VENTA NO VIENE DE UNA SIMULACION, HAGO EL TRATAMIENTO DE ANTES
            if not sale_order.simulation_cost_ids:
                #
                ### Llamo con SUPER al método padre
                task_id = super(procurement_order, self).action_produce_assign_service(cr, uid, [procurement.id], context=None)             
            else:
                ### SI EL PEDIDO DE VENTA VIENE DE UNA SIMULACION
                if not sale_order_line.simulation_cost_line_ids:
                    ### SI LA LINEA DEL PEDIDO DE VENTA NO VIENE DE UNA LINEA DE 
                    ### SIMULACION DE COSTE, Y TAMPOCO VIENE DE PREVISIONES
                    ###
                    ### Llamo a esta función para validar el subproyecto, y aprovecho
                    ### para imputar en cuenta y eb subcuenta analítica, los costes y
                    ### beneficios estimados, parámetro type=1 significa que la línea
                    ### del pedido de venta no viene de simulación de costes
                    w_sale_order_name = sale_order.name
                    w_template_id = 0
                    w_account_analytic_account_id = account_analytic_account_id
                    w_imp_purchase = planned_hours * product.standard_price
                    w_imp_sale = planned_hours * product.list_price 
                    w_type = 1
                    project_subproject_id = self._project_validate_subproject_analytic_account(cr, uid, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)                                 
                    # DOY DE ALTA LA TAREA PARA EL SUBPROYECTO
                    project_task = self.pool.get('project.task')
                    task_id = project_task.create(cr, uid, {'name': '%s:%s' % (procurement.origin or '', procurement.product_id.name),
                                                            'date_deadline': procurement.date_planned,
                                                            'planned_hours': planned_hours,
                                                            'remaining_hours': planned_hours,
                                                            'user_id': procurement.product_id.product_manager.id,
                                                            'notes': procurement.note,
                                                            'procurement_id': procurement.id,
                                                            'description': procurement.note,
                                                            'project_id':  project_subproject_id,
                                                            'company_id': procurement.company_id.id,
                                                            },context=context)   
                    self.write(cr, uid, [procurement.id], {'task_id': task_id, 'state': 'running'}, context=context)                       

          
                else:        
                    ### SI LA LINEA DEL PEDIDO DE VENTA, VIENE DE UNA LINEA DE
                    ### SIMULACIÓN DE COSTE, TRATO TODAS LA LINEAS DE SIMULACION DE COSTE
                    for simulation_cost_line in  sale_order_line.simulation_cost_line_ids:
                        # Si la linea del pedido de venta no viene de previsiones, y la
                        # linea de simulación no tiene asociado un pedido de compra
                        if not simulation_cost_line.purchase_order_id:                       
                            # Si la linea de simulación de coste, se corresponde con la linea
                            # de simulación de coste perteneciente a la simulación de coste activa
                            # o a la última historificada, trato la linea.
                            if simulation_cost_line.simulation_cost_id.id == w_simulation_cost_id:
                                # SI LA LINEA DE SIMULACIÓN DE COSTE, NO VIENE DE UNA LINEA
                                # DE PLANTILLA DE SIMULACION
                                if not simulation_cost_line.template_id:
                                    product_obj = self.pool.get('product.product')
                                    cost_product = product_obj.browse(cr, uid, simulation_cost_line.product_id.id)
                                    #raise osv.except_osv('Purchase Order Creation Error', 'Task: ' +  product.name + 'without Simulation Template')
                                    ###
                                    ### Llamo a esta función para validar el subproyecto, y provecho
                                    ### para imputar en cuenta y eb subcuenta analítica, los costes y
                                    ### beneficios estimados, parámetro type=2 significa que la línea
                                    ### del pedido de venta viene de simulación de coste, pero la línea
                                    ### de simulación de coste de la que viene, no está asociada a 
                                    ### ninguna plantilla de simulación
                                    w_sale_order_name = sale_order.name
                                    w_template_id = 0
                                    w_account_analytic_account_id = account_analytic_account_id
                                    w_imp_purchase = simulation_cost_line.subtotal_purchase
                                    w_imp_sale = simulation_cost_line.subtotal_sale
                                    w_type = 2
                                    project_subproject_id = self._project_validate_subproject_analytic_account(cr, uid, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                                else:
                                    # SI LA LINEA DE SIMULACIÓN DE COSTE VIENE DE UNA LINEA
                                    # DE PLANTILLA DE SIMULACION
                                    ###
                                    ### Llamo a esta función para validar el subproyecto, y provecho
                                    ### para imputar en cuenta y eb subcuenta analítica, los costes y
                                    ### beneficios estimados, parámetro type=3 significa que la línea
                                    ### del pedido de venta viene de simulación de coste, y que la línea
                                    ### de simulación de coste de la que viene, está asociada a línea
                                    ### de plantilla de simulación
                                    w_sale_order_name = sale_order.name
                                    w_template_id = simulation_cost_line.template_id.id
                                    w_account_analytic_account_id = account_analytic_account_id
                                    w_imp_purchase = simulation_cost_line.subtotal_purchase
                                    w_imp_sale = simulation_cost_line.subtotal_sale
                                    w_type = 3
                                    project_subproject_id = self._project_validate_subproject_analytic_account(cr, uid, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
    
                                # COJO EL NOMBRE DEL PRODUCTO DE VENTA DE LA LINEA DE SIMULACION DE COSTES
                                product_obj = self.pool.get('product.product')
                                cost_product = product_obj.browse(cr, uid, simulation_cost_line.product_id.id)
                                sale_product = product_obj.browse(cr, uid, simulation_cost_line.product_sale_id.id)
                                
                                # DOY DE ALTA LA TAREA PARA EL SUBPROYECTO
                                project_task = self.pool.get('project.task')
                                task_id = project_task.create(cr, uid, {'name': simulation_cost_line.name,
                                                                        'date_deadline': procurement.date_planned,
                                                                        'planned_hours': simulation_cost_line.amount,
                                                                        'remaining_hours': simulation_cost_line.amount,
                                                                        'user_id': simulation_cost_line.product_id.product_manager.id,
                                                                        'notes': procurement.note,
                                                                        'procurement_id': procurement.id,
                                                                        'description': procurement.note,
                                                                        'project_id':  project_subproject_id,
                                                                        'company_id': procurement.company_id.id,
                                                                        'cost_product_name': cost_product.name,
                                                                        'sale_product_name': sale_product.name,
                                                                        },context=context)
                                self.write(cr, uid, [procurement.id], {'task_id': task_id, 'state': 'running'}, context=context) 


        return task_id         
    
    #
    ### Funcion para validar que existe la subcuenta analitica,
    ### si no existe la subcuenta analitica la crea, y tambien
    ### crea su subproyecto.
    ### En esta funcion tambien se realiza la imputacion de la
    ### estimacion de costes y beneficios en la subcuenta analitica
#    def _validate_subproject_analytic_account(self, cr, uid, ids, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale, context=None):
    def _project_validate_subproject_analytic_account(self, cr, uid, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale):
        #
        ### Voy a generar el literal a buscar en subcuenta analítica
        w_literal = ''
        #
        # Cojo el nombre de la simulacion de costes
        simulation_cost_obj = self.pool.get('simulation.cost') 
        simulation_cost = simulation_cost_obj.browse(cr, uid, w_simulation_cost_id)
        #
        ### type=1 significa que la línea del pedido de venta, no viene de
        ### simulación de costes
        if w_type == 1:
            # Genero el literal
            w_literal = 'SUBP ' + simulation_cost.simulation_number + ' / NO FROM Simulation Cost / ' + w_sale_order_name
        #
        ### type=2 significa que la línea del pedido de venta viene de una
        ### simulación de costes, pero la línea de simulación de costes de
        ### la que viene, no está asociada a ninguna plantilla de simulación
        if w_type == 2:
            # Genero el literal
            w_literal = 'SUBP ' + simulation_cost.simulation_number + ' / NO FROM Simulation Template / ' + w_sale_order_name              
            
        ### type=3 significa que la línea del pedido de venta viene de simulación
        ### de coste, y que la línea de simulación de coste de la que viene, esta
        ### asociada a línea de plantilla de simulación
        if w_type == 3:
            # Cojo el nombre de la plantilla de simulación
            simulation_template_obj = self.pool.get('simulation.template') 
            simulation_template = simulation_template_obj.browse(cr, uid, w_template_id)
            # Genero el literal a buscar
            w_literal = 'SUBP ' + simulation_cost.simulation_number + ' / ' + simulation_template.name + ' / ' + w_sale_order_name

        #
        # CON EL LITERAL GENERADO, BUSCO LA SUBCUENTA ANALÍTICA PARA VER
        # SI EXISTE O NO    
        sub_account_analytic_account_obj = self.pool.get('account.analytic.account')
        sub_account_analytic_account_ids = sub_account_analytic_account_obj.search(cr, uid,[('name','=', w_literal)])
        # En este punto debería o no de haber encontrado 1 sola subcuenta analítica
        w_found = 0
        for sub_account_analytic_account in sub_account_analytic_account_ids:
            # Si existe la subcuenta analítica, cojo su ID
            w_found = 1
            sub_account_analytic_account_id = sub_account_analytic_account
                             
        # Si no encuentro el subproyecto, lo creo
        if w_found == 0:
            if w_type == 3:
                raise osv.except_osv('Purchase Order Creation Error', 'Subaccount analytic account not found, literal: ' + w_literal)
            else:
                line = {'name' : w_literal,
                        'parent_id':  w_account_analytic_account_id,
                        'type': 'normal',
                        'state': 'open',
                        'estimated_balance': 0,
                        'estimated_cost': 0,
                        'estimated_sale': 0,
                        }
                account_analytic_account_obj = self.pool.get('account.analytic.account')
                sub_account_analytic_account_id = account_analytic_account_obj.create(cr, uid, line)

        # MODIFICACION DE LA CUENTA ANALÍTICA (DEL PROYECTO)
        account_analytic_account_obj2 = self.pool.get('account.analytic.account')
        account_analytic_account2 = account_analytic_account_obj2.browse(cr, uid, w_account_analytic_account_id)
        w_estimated_cost = account_analytic_account2.estimated_cost
        w_estimated_cost = w_estimated_cost + w_imp_purchase
        w_estimated_sale = account_analytic_account2.estimated_sale
        w_estimated_sale = w_estimated_sale + w_imp_sale
        w_estimated_balance = w_estimated_sale - w_estimated_cost
        account_analytic_account_obj2.write(cr, uid, [w_account_analytic_account_id], {'estimated_cost': w_estimated_cost,
                                                                                       'estimated_sale': w_estimated_sale,
                                                                                       'estimated_balance': w_estimated_balance})
        # MODIFICACION DE LA SUBCUENTA ANALÍTICA (DEL SUBPROYECTO)
        sub_account_analytic_account_obj2 = self.pool.get('account.analytic.account')
        sub_account_analytic_account2 = sub_account_analytic_account_obj2.browse(cr, uid, sub_account_analytic_account_id)
        w_estimated_cost = sub_account_analytic_account2.estimated_cost
        w_estimated_cost = w_estimated_cost + w_imp_purchase
        w_estimated_sale = sub_account_analytic_account2.estimated_sale
        w_estimated_sale = w_estimated_sale + w_imp_sale
        w_estimated_balance = w_estimated_sale - w_estimated_cost
        sub_account_analytic_account_obj2.write(cr, uid, [sub_account_analytic_account_id], {'estimated_cost': w_estimated_cost,
                                                                                             'estimated_sale': w_estimated_sale,
                                                                                             'estimated_balance': w_estimated_balance})

        # BUSCO LA SUBCUENTA ANALÍTICA PARA LA PESTAÑA 'internal task'
        w_literal2 = w_literal + ' (Internal Task)'
            
        sub_account_analytic_account_obj3 = self.pool.get('account.analytic.account')
        sub_account_analytic_account_ids3 = sub_account_analytic_account_obj3.search(cr, uid,[('name','=', w_literal2),
                                                                                              ('parent_id','=', sub_account_analytic_account_id)])
            
        if sub_account_analytic_account_ids3:
            # Si ha encontrado alguna linea, solo habrá encontrado 1,
            # ya que esta buscado una cuenta en concreto, así que me 
            # quedo con su ID
            sub_account_analytic_account_id2 = sub_account_analytic_account_ids3[0]
            project_project_obj = self.pool.get('project.project')
            project_id = project_project_obj.search(cr, uid,[('name','=', w_literal2)]) 
            if not project_id:
                raise osv.except_osv('Purchase Order Creation Error','subproject not found(2), literal: ' + w_literal2)
            else:
                project_subproject_id = project_id[0]           
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
                account_analytic_account_obj = self.pool.get('account.analytic.account')
                sub_account_analytic_account_id2 = account_analytic_account_obj.create(cr, uid, line)
                # ahora creo el subproyecto
                line = {'name' : w_literal2,
                        'analytic_account_id': sub_account_analytic_account_id2,
                }          
                project_project_obj = self.pool.get('project.project')
                project_subproject_id = project_project_obj.create(cr, uid, line) 

 
        # UNA VEZ LLEGADO A ESTE PUNTO, YA PUEDO HACER LA IMPUTACION DE LAS ESTIMACIONES
        # A LA SUBCUENTA ANALITICA PERTENECIENTE A LA PESTAÑA DE LA SIMULACION DE COSTES
        sub_account_analytic_account_obj2 = self.pool.get('account.analytic.account')
        sub_account_analytic_account2 = sub_account_analytic_account_obj2.browse(cr, uid, sub_account_analytic_account_id2)
        w_estimated_cost = sub_account_analytic_account2.estimated_cost
        w_estimated_cost = w_estimated_cost + w_imp_purchase
        w_estimated_sale = sub_account_analytic_account2.estimated_sale
        w_estimated_sale = w_estimated_sale + w_imp_sale
        w_estimated_balance = w_estimated_sale - w_estimated_cost
        sub_account_analytic_account_obj2.write(cr, uid, [sub_account_analytic_account_id2], {'estimated_cost': w_estimated_cost,                                                                                        
                                                                                              'estimated_sale': w_estimated_sale,
                                                                                              'estimated_balance': w_estimated_balance})    
            
        return project_subproject_id 

procurement_order()