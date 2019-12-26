# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields
# from tools.translate import _
# import time
# import netsvc


from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'
     
    # Campo para saber con que costes de simulación está relacionada
    simulation_cost_ids = fields.Many2many(
        comodel_name='simulation.cost',
        relation='simucost_saleorder_rel',
        column1='simulation_cost_id',
        column2='sale_order_id',
        string='Simulation Costs',
        readonly=True)
    # Campo para relacionar el proyecto con el pedido de venta, la relacion es de 1 a 1
    project2_id = fields.Many2one(
        comodel_name='project.project',
        string='Project')
    # Campo para saber que pedidos de compra se han generado a partir de
    # este pedido de venta
    purchase_order_ids = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='sale_order_id',
        string="Purchase Orders")

    #
    ### Heredo la función que crea albaranes y abastecimientos
    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Create the required procurements to supply sale order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sale order's requested location.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: sale order to which the order lines belong
        :param list(browse_record) order_lines: sale order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []

        for line in order_lines:
            if line.state == 'done':
                continue

            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
            
            if line.product_id:
                if line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                else:
                    # a service has no stock move
                    move_id = False
                if line.clear_procurement == False:
                    proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
                    proc_ids.append(proc_id)
                    line.write({'procurement_id': proc_id})
                    self.ship_recreate(cr, uid, order, line, move_id, proc_id)

        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)

        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False

            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val)
        
        return True
   
    #
    ### FUNCION QUE SE EJECUTA CUANDO CONFIRMO UN PEDIDO DE VENTA
    def action_wait(self, cr, uid, ids, context=None):      
        if not context:
            context ={}
        sale_order_obj = self.pool.get('sale.order') 
        simulation_template_obj = self.pool.get('simulation.template')
        sale_order_line_obj = self.pool.get('sale.order.line')
        ### Accedo al PEDIDO DE VENTA
        sale_order2 = sale_order_obj.browse(cr, uid, ids[0])   
        #
        ### Recorro las lineas de pedido de venta, si el producto de la linea 
        ### tiene como metodo de abastecimiento OBTENER PARA STOCK, lo marco
        ### para que no genere una excepción de abastecimiento
        for sale_order_line in sale_order2.order_line:
            if sale_order_line.product_id.procure_method == 'make_to_stock':
                sale_order_line_obj.write(cr,uid,[sale_order_line.id],{'clear_procurement': True})  
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
                    raise osv.except_osv(_('Project Creation Error'),_('Simulation Cost not found'))
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
                
                # 
                # DOY DE ALTA EL PROYECTO
                #
                line = {'name' : 'PROJ ' + simulation_cost.simulation_number + ' / ' + sale_order2.name,
                        'partner_id': sale_order2.partner_id.id,
                        'simulation_cost_id': simulation_cost.id,
                        'is_project': True
                        }
                project_project_obj = self.pool.get('project.project')
                project_project_id = project_project_obj.create(cr, uid, line)   
                
                # Actualizo la cuenta analitica que se ha dado de alta automaticamente al crear el proyecto
                project = project_project_obj.browse(cr, uid, project_project_id)
                account_analytic_account_obj = self.pool.get('account.analytic.account')
                account_analytic_account_obj.write(cr,uid,[project.analytic_account_id.id],{'name' : 'PROJ ' + simulation_cost.simulation_number + ' / ' + sale_order2.name,
                                                                                            'type': 'view',
                                                                                            'state': 'open',
                                                                                            'estimated_balance': 0,
                                                                                            'estimated_cost': 0,
                                                                                            'estimated_sale': 0,
                                                                                            'partner_id': sale_order2.partner_id.id,
                                                                                            })

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
                    if simulation_cost_line.template_id:     
                        if simulation_cost_line.sale_order_line_id.order_id.id == sale_order2.id:
                            simulation_template_obj = self.pool.get('simulation.template') 
                            simulation_template = simulation_template_obj.browse(cr, uid, simulation_cost_line.template_id.id)
                            w_literal = 'SUBP ' + simulation_cost.simulation_number + ' / ' + simulation_template.name + ' / ' + sale_order2.name
                            # Miro si existe la subcuenta analitica
                            account_analytic_account_ids = account_analytic_account_obj.search(cr, uid,[('name','=', w_literal)])
                            if not account_analytic_account_ids:
                                # Si no existe el subproyecto lo doy de alta
                                line = {'name' : w_literal,
                                        'parent_id': project.analytic_account_id.id,
                                        'partner_id': sale_order2.partner_id.id,
                                        'is_subproject': True
                                        }
                                subproject_project_id = project_project_obj.create(cr, uid, line)                          
                                # Actualizo la subcuenta analitica creada desde el suproyecto
                                subproject = project_project_obj.browse(cr, uid, subproject_project_id)
                                w_sub_account_analytic_account_id = subproject.analytic_account_id.id
                                account_analytic_account_obj.write(cr,uid,[w_sub_account_analytic_account_id],{'name' : w_literal,
                                                                                                               'type': 'normal',
                                                                                                               'state': 'open',
                                                                                                               'estimated_balance': 0,
                                                                                                               'estimated_cost': 0,
                                                                                                               'estimated_sale': 0,
                                                                                                               })   
                                # Borro el subproyecto creado, ya que no nos interesa tenerlo, solo nos interesa 
                                # tener la subcuenta analítica  
                                project_project_obj.unlink(cr, uid, [subproject.id])
                            else:
                                w_sub_account_analytic_account_id = account_analytic_account_ids[0]
                                
                            #
                            ### Trato la pestaña Purchase
                            if simulation_cost_line.type_cost == 'Purchase':
                                w_literal2 = w_literal + ' (Purchase)'
                                project_ids = project_project_obj.search(cr, uid,[('name','=', w_literal2)])
                                if not project_ids:
                                    # Si no existe el subproyecto lo doy de alta
                                    line = {'name' : w_literal2,
                                            'parent_id': w_sub_account_analytic_account_id,
                                            'partner_id': sale_order2.partner_id.id,
                                            'simulation_cost_id2': w_simulation_cost_id
                                            }
                                    subproject_project_id = project_project_obj.create(cr, uid, line)                          
                                    # Actualizo la subcuenta analitica creada desde el suproyecto
                                    subproject = project_project_obj.browse(cr, uid, subproject_project_id)
                                    w_sub_account_analytic_account_id = subproject.analytic_account_id.id
                                    account_analytic_account_obj.write(cr,uid,[w_sub_account_analytic_account_id],{'name' : w_literal2,
                                                                                                                   'type': 'normal',
                                                                                                                   'state': 'open',
                                                                                                                   'estimated_balance': 0,
                                                                                                                   'estimated_cost': 0,
                                                                                                                   'estimated_sale': 0,
                                                                                                                   })     
                            #
                            ### Trato la pestaña Investment
                            if simulation_cost_line.type_cost == 'Investment':
                                w_literal2 = w_literal + ' (Investment)'
                                project_ids = project_project_obj.search(cr, uid,[('name','=', w_literal2)])
                                if not project_ids:
                                    # Si no existe el subproyecto lo doy de alta
                                    line = {'name' : w_literal2,
                                            'parent_id': w_sub_account_analytic_account_id,
                                            'partner_id': sale_order2.partner_id.id,
                                            'simulation_cost_id2': w_simulation_cost_id
                                            }
                                    subproject_project_id = project_project_obj.create(cr, uid, line)                          
                                    # Actualizo la subcuenta analitica creada desde el suproyecto
                                    subproject = project_project_obj.browse(cr, uid, subproject_project_id)
                                    w_sub_account_analytic_account_id = subproject.analytic_account_id.id
                                    account_analytic_account_obj.write(cr,uid,[w_sub_account_analytic_account_id],{'name' : w_literal2,
                                                                                                                   'type': 'normal',
                                                                                                                   'state': 'open',
                                                                                                                   'estimated_balance': 0,
                                                                                                                   'estimated_cost': 0,
                                                                                                                   'estimated_sale': 0,
                                                                                                                   })                                  
                            #
                            ### Trato la pestaña Subcontracting Services
                            if simulation_cost_line.type_cost == 'Subcontracting Services':
                                w_literal2 = w_literal + ' (Subcontracting Services)'
                                project_ids = project_project_obj.search(cr, uid,[('name','=', w_literal2)])
                                if not project_ids:
                                    # Si no existe el subproyecto lo doy de alta
                                    line = {'name' : w_literal2,
                                            'parent_id': w_sub_account_analytic_account_id,
                                            'partner_id': sale_order2.partner_id.id,
                                            'simulation_cost_id2': w_simulation_cost_id
                                            }
                                    subproject_project_id = project_project_obj.create(cr, uid, line)                          
                                    # Actualizo la subcuenta analitica creada desde el suproyecto
                                    subproject = project_project_obj.browse(cr, uid, subproject_project_id)
                                    w_sub_account_analytic_account_id = subproject.analytic_account_id.id
                                    account_analytic_account_obj.write(cr,uid,[w_sub_account_analytic_account_id],{'name' : w_literal2,
                                                                                                                   'type': 'normal',
                                                                                                                   'state': 'open',
                                                                                                                   'estimated_balance': 0,
                                                                                                                   'estimated_cost': 0,
                                                                                                                   'estimated_sale': 0,
                                                                                                                   })     
                            #
                            ### Trato la pestaña Others
                            if simulation_cost_line.type_cost == 'Others':
                                w_literal2 = w_literal + ' (Others)'
                                project_ids = project_project_obj.search(cr, uid,[('name','=', w_literal2)])
                                if not project_ids:
                                    # Si no existe el subproyecto lo doy de alta
                                    line = {'name' : w_literal2,
                                            'parent_id': w_sub_account_analytic_account_id,
                                            'partner_id': sale_order2.partner_id.id,
                                            'simulation_cost_id2': w_simulation_cost_id
                                            }
                                    subproject_project_id = project_project_obj.create(cr, uid, line)                          
                                    # Actualizo la subcuenta analitica creada desde el suproyecto
                                    subproject = project_project_obj.browse(cr, uid, subproject_project_id)
                                    w_sub_account_analytic_account_id = subproject.analytic_account_id.id
                                    account_analytic_account_obj.write(cr,uid,[w_sub_account_analytic_account_id],{'name' : w_literal2,
                                                                                                                   'type': 'normal',
                                                                                                                   'state': 'open',
                                                                                                                   'estimated_balance': 0,
                                                                                                                   'estimated_cost': 0,
                                                                                                                   'estimated_sale': 0,
                                                                                                                   })     
                            #
                            ### Trato la pestaña Task
                            if simulation_cost_line.type_cost == 'Task':
                                w_literal2 = w_literal + ' (Internal Task)'
                                project_ids = project_project_obj.search(cr, uid,[('name','=', w_literal2)])
                                if not project_ids:
                                    # Si no existe el subproyecto lo doy de alta
                                    line = {'name' : w_literal2,
                                            'parent_id': w_sub_account_analytic_account_id,
                                            'partner_id': sale_order2.partner_id.id,
                                            'simulation_cost_id2': w_simulation_cost_id
                                            }
                                    subproject_project_id = project_project_obj.create(cr, uid, line)                          
                                    # Actualizo la subcuenta analitica creada desde el suproyecto
                                    subproject = project_project_obj.browse(cr, uid, subproject_project_id)
                                    w_sub_account_analytic_account_id = subproject.analytic_account_id.id
                                    account_analytic_account_obj.write(cr,uid,[w_sub_account_analytic_account_id],{'name' : w_literal2,
                                                                                                                   'type': 'normal',
                                                                                                                   'state': 'open',
                                                                                                                   'estimated_balance': 0,
                                                                                                                   'estimated_cost': 0,
                                                                                                                   'estimated_sale': 0,
                                                                                                                   })                                 
                
                # SI NO VENGO DEL MÓDULO avanzosc_costs_simulator_purchase_requisition         
                if not context.has_key('from_purchase_requisition'):                          
                    #
                    ### Si el pedido de venta viene de una simulacion, y las lineas de pedido de venta
                    ### tienen productos que definin una plantilla de simulación, genero pedidos y tareas
                    if sale_order2.simulation_cost_ids:
                        for sale_order_line in sale_order2.order_line:
                            if sale_order_line.simulation_cost_line_ids:
                                w_found = 0
                                w_cont  = 0
                                for simulation_cost_line in sale_order_line.simulation_cost_line_ids:
                                    if simulation_cost_line.simulation_cost_id.id == w_simulation_cost_id:
                                        w_cont = w_cont + 1
                                        if simulation_cost_line.template_id:
                                            if simulation_cost_line.template_id.template_product_id:
                                                if sale_order_line.product_id.id == simulation_cost_line.template_id.template_product_id.id:
                                                    w_found = w_found + 1
                                if w_found > 0:
                                    ### Genero pedidos de compra y tareas
                                    if w_found == w_cont:
                                        # Indico que no tiene que generar excepciones de abastecimiento
                                        sale_order_line_obj.write(cr,uid,[sale_order_line.id],{'clear_procurement': True})                                          
                                        #
                                        ### Genero pedidos y tareas
                                        for simulation_cost_line in sale_order_line.simulation_cost_line_ids:
                                            w_clean_procurement_order = 0
                                            if simulation_cost_line.product_id.type == 'product' or simulation_cost_line.product_id.type == 'consu':
                                                if simulation_cost_line.simulation_cost_id.id == w_simulation_cost_id:
                                                    w_clean_procurement_order = 1
                                                    self._generate_purchase_order(cr, uid, project_project_id, sale_order2, w_simulation_cost_id, simulation_cost_line, project.analytic_account_id.id, context)
                                            else:
                                                if simulation_cost_line.product_id.type == 'service' and simulation_cost_line.product_id.procure_method != 'make_to_stock':
                                                    if simulation_cost_line.product_id.supply_method == 'buy':
                                                        if simulation_cost_line.simulation_cost_id.id == w_simulation_cost_id:
                                                            w_clean_procurement_order = 1
                                                            self._generate_purchase_order(cr, uid, project_project_id, sale_order2, w_simulation_cost_id, simulation_cost_line, project.analytic_account_id.id, context)                              
                                                    else:
                                                        if simulation_cost_line.product_id.supply_method == 'produce':
                                                            if simulation_cost_line.simulation_cost_id.id == w_simulation_cost_id:
                                                                w_clean_procurement_order = 1
                                                                self._generate_project_task(cr, uid, sale_order2, project_project_id, w_simulation_cost_id, simulation_cost_line, project.analytic_account_id.id, context)
        
        
        super(sale_order,self).action_wait(cr, uid, ids, context)
                                            
        return True  
    
    def _generate_purchase_order(self, cr, uid, project_project_id, sale_order, w_simulation_cost_id, simulation_cost_line, account_analytic_account_id, context=None):
        res = {}
        if context is None:
            context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        partner_obj = self.pool.get('res.partner')
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        prod_obj = self.pool.get('product.product')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        seq_obj = self.pool.get('ir.sequence')
        warehouse_obj = self.pool.get('stock.warehouse')
        purchase_order_obj = self.pool.get('purchase.order') 
        simulation_cost_obj = self.pool.get('simulation.cost')
        project_project_obj = self.pool.get('project.project')

        simulation_cost = simulation_cost_obj.browse(cr,uid,w_simulation_cost_id)
        
        if simulation_cost_line.supplier_id:
            ### SI EL PRODUCTO VIENE CON UN PROVEEDOR EN CONTRETO, TRATO ESE PROVEEDOR 
            #
            ### MIRO SI YA EXISTE UN PEDIDO DE COMPRA PARA ESTE PROVEEDOR QUE VIENE 
            ### EN LA LÍNEA  
            purchase_order_id = purchase_order_obj.search(cr, uid,[('sale_order_id','=', sale_order.id),
                                                                   ('partner_id', '=', simulation_cost_line.supplier_id.id),
                                                                   ('state', '=', 'draft'),     
                                                                   ('type_cost','=', simulation_cost_line.type_cost)])
            res_id = False
            partner = simulation_cost_line.supplier_id
            qty = simulation_cost_line.amount
            partner_id = partner.id
            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id
            warehouse_id = sale_order.shop_id.warehouse_id.id
            uom_id = simulation_cost_line.uom_id.id
            price = simulation_cost_line.purchase_price
            schedule_date = time.strftime('%Y-%m-%d')
            purchase_date = time.strftime('%Y-%m-%d')
            context.update({'lang': partner.lang, 'partner_id': partner_id})
            product = prod_obj.browse(cr, uid, simulation_cost_line.product_id.id, context=context)
            taxes_ids = simulation_cost_line.product_id.product_tmpl_id.supplier_taxes_id
            taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
            ###
            ### Llamo a esta función para validar el subproyecto, y aprovecho
            ### para imputar en cuenta y en subcuenta analítica, los costes y
            ### beneficios estimados.
            ### type=1 es una caso especial, porque la línea de
            ### pedido de venta no proviene de una simulación de costes,
            ### por tanto no sé a que pestaña de simulación de costes
            ### proviene (purchase, investment, subcontracting, others)
            ### type=2 significa que la línea del pedido de venta
            ### no proviene de una plantilla de simulacion, y type=3
            ### significa que la línea de pedido de venta proviene
            ### de una plantilla de simulación                            
            w_sale_order_name = sale_order.name
            w_account_analytic_account_id = account_analytic_account_id
            w_imp_purchase = simulation_cost_line.subtotal_purchase
            w_imp_sale = simulation_cost_line.subtotal_sale
            w_text = simulation_cost_line.type_cost
            # Si la línea de simulación de coste viene de una línea de plantilla de simulación
            # le paso su ID
            w_template_id = simulation_cost_line.template_id.id
            w_type = 3

            # Al venir el producto con un proveedor en concreto, sumo el importe
            # de coste a analítica, eso lo indico poniento w_sum_analitic = 1
            w_sum_analitic = 1
            #
            account_id = self._sale_order_purchase_validate_subproject_analytic_account(cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale) 
            if not purchase_order_id:
                #
                ### SI NO EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR
                line_vals = {'name': simulation_cost_line.name,
                             'product_qty': qty,
                             'product_id': simulation_cost_line.product_id.id,
                             'product_uom': uom_id,
                             'price_unit': price or 0.0,
                             'date_planned': time.strftime('%Y-%m-%d'),
                             'move_dest_id': res_id,
                             'notes': product.description_purchase,
                             'taxes_id': [(6,0,taxes)],
                             }
                #
                ### Cojo el tipo de pedido de compra
                purchase_type_obj = self.pool.get('purchase.type')
                if simulation_cost_line.type_cost == 'Purchase':
                    purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Purchase')])
                    if not purchase_type_ids:
                        raise osv.except_osv(_('Purchase Order Error'),_('Purchase literal not found in Table Purchase Type'))
                if simulation_cost_line.type_cost == 'Investment':
                    purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Investment')])
                    if not purchase_type_ids:
                        raise osv.except_osv(_('Purchase Order Error'),_('Invesment literal not found in Table Purchase Type'))
                if simulation_cost_line.type_cost == 'Subcontracting Services':
                    purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Subcontracting Services')])
                    if not purchase_type_ids:
                        raise osv.except_osv(_('Purchase Order Error'),_('Subcontracting Services literal not found in Table Purchase Type'))
                if simulation_cost_line.type_cost == 'Task':
                    purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Tasks')])
                    if not purchase_type_ids:
                        raise osv.except_osv(_('Purchase Order Error'),_('Task literal not found in Table Purchase Type'))
                if simulation_cost_line.type_cost == 'Others':
                    purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Others')])
                    if not purchase_type_ids:
                        raise osv.except_osv(_('Purchase Order Error'),_('Others literal not found in Table Purchase Type'))

                purchase_type = purchase_type_obj.browse(cr, uid, purchase_type_ids[0])
                
                ### COJO LA SECUENCIA
                code = purchase_type.sequence.code
                name = self.pool.get('ir.sequence').get(cr,uid,code)                                                             
        
                po_vals = {'name': name,
                           'origin': sale_order.name + ' - ' + simulation_cost.simulation_number,
                           'partner_id': partner_id,
                           'partner_address_id': address_id,
                           'location_id': sale_order.shop_id.warehouse_id.lot_stock_id.id,
                           'warehouse_id': warehouse_id or False,
                           'pricelist_id': pricelist_id,
                           'date_order': time.strftime('%Y-%m-%d'),
                           'company_id': company.id,
                           'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                           'type': purchase_type.id,
                           'type_cost': simulation_cost_line.type_cost
                           }
                pc = self._sale_order_create_purchase_order(cr, uid, po_vals, line_vals, context=context)
                #
                ### AÑADO EL ID DEL SUBPROYECTO AL PEDIDO DE COMPRA
                purchase_order_obj.write(cr,uid,[pc],{'sale_order_id': sale_order.id,
                                                      'project3_id': project_project_id})  
                #
                ### COJO EL ID DE LA LINEA DE PEDIDO DE COMPRA QUE SE HA DADO DE ALTA    
                purchase_order_line_obj = self.pool.get('purchase.order.line') 
                purchase_order_line_ids = purchase_order_line_obj.search(cr, uid,[('order_id','=', pc)])
                if not purchase_order_line_ids:
                    raise osv.except_osv(_('Purchase Order Creation Error'),_('Purchase Order Line not found(2)'))
                else:
                    purchase_order_line_id = purchase_order_line_ids[0]     
                purchaseorder_id = pc
            else:
                #
                ### SI EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR
                ### DOY DE ALTA UNA LINEA EN LA LINEA DE PEDIDOS DE COMPRA
                line_vals = {'name': simulation_cost_line.name,
                             'order_id': purchase_order_id[0],
                             'product_qty': qty,
                             'product_id': simulation_cost_line.product_id.id,
                             'product_uom': uom_id,
                             'price_unit': price or 0.0,
                             'date_planned': time.strftime('%Y-%m-%d'),
                             'move_dest_id': res_id,
                             'notes': product.description_purchase,
                             'taxes_id': [(6,0,taxes)],
                             }   

                purchase_order_line_obj = self.pool.get('purchase.order.line') 
                purchase_order_line_id = purchase_order_line_obj.create(cr, uid, line_vals)     
                purchaseorder_id = purchase_order_id[0]
            
            ###
            ### Llamo a esta función para imputar los costes estimados 
            ### a la subcuenta analítica expresa de la pestaña de
            ### simulación de costes de la que proviene.
            ### Además de imputar los costes estimados, también relacionará
            ### la línea del pedido de compra, con la subcuenta analítica
            ### que le corresponde.
            ### type=1 es una caso especial, porque la línea de
            ### pedido de venta no proviene de una simulación de costes,
            ### por tanto no sé a que pestaña de simulación de costes
            ### proviene (purchase, investment, subcontracting, others)
            ### type=2 significa que la línea del pedido de venta
            ### no proviene de una plantilla de simulacion, y type=3
            ### significa que la línea de pedido de venta proviene
            ### de una plantilla de simulación
            w_sale_order_name = sale_order.name
            w_account_analytic_account_id = account_analytic_account_id
            w_imp_purchase = simulation_cost_line.subtotal_purchase
            w_imp_sale = simulation_cost_line.subtotal_sale
            # Si la línea de simulación de coste viene de una línea de plantilla de simulación
            w_template_id = simulation_cost_line.template_id.id
            # En este campo le paso el texto del tipo de coste
            # (purchase, investment, subcontracting, task, o others)
            w_text = simulation_cost_line.type_cost
            w_purchase_order_line_id = purchase_order_line_id
            w_type = 3

            # Al venir el producto con un proveedor en concreto, sumo el importe
            # de coste a analítica, eso lo indico poniento w_sum_analitic = 1
            w_sum_analitic = 1
            #
            subanalytic_account_id = self._sale_order_purchase_validate_subanalytic_account(cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id,w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
            subproject_ids = project_project_obj.search(cr, uid,[('analytic_account_id','=', subanalytic_account_id)])
            purchase_order_obj.write(cr,uid,[purchaseorder_id],{'project2_id': subproject_ids[0]}) 
        else: 
            ### SI EL PRODUCTO NO VIENE CON UN PROVEEDOR EN CONCRETO, TRATO TODOS SUS PROVEEDORES    
            supplierinfo_obj = self.pool.get('product.supplierinfo')
            supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', simulation_cost_line.product_id.id)],                                                                 
                                                       order='sequence')

            if not supplierinfo_ids:
                # Si no hay proveedores definidos para el producto, muestro el error
                raise osv.except_osv(_('Purchase Order Creation Error'),_('You must define one supplier for the product: ' + simulation_cost_line.product_id.name))
            else:
                # TRATO TODOS LOS PROVEEDORES ENCONTRADOS PARA EL PRODUCTO,
                # CREARE UN PEDIDO DE COMPRA PARA CADA PROVEEDOR DE ESE
                # PRODUCTO
                #
                # Como el producto no viene con un proveedor en concreto, debo de grabar
                # un pedido de compra por cada proveedor, es por ello que inicializo el 
                # campo w_sum_analitic a 0, e iré sumando 1 a este campo por cada proveedor
                # que trate de ese producto, de esta manera solo imputaré a cuentas analíticas
                # 1 única vez
                w_sum_analitic = 0                                       
                #
                for supplierinfo in supplierinfo_ids:
                    supplierinfo_id = supplierinfo_obj.browse(cr, uid, supplierinfo)
                    partner = self.pool.get('res.partner')
                    supplier = partner.browse(cr, uid, supplierinfo_id.name.id)                             
                    ###
                    ### MIRO SI YA EXISTE UN PEDIDO DE COMPRA PARA EL PROVEEDOR QUE VE VIENE 
                    ### DE LA BUSQUEDA ANTERIOR
                    purchase_order_obj = self.pool.get('purchase.order')
                    purchase_order_id = purchase_order_obj.search(cr, uid,[('sale_order_id','=', sale_order.id),
                                                                           ('partner_id', '=', supplier.id),
                                                                           ('state', '=', 'draft'),     
                                                                           ('type_cost','=', simulation_cost_line.type_cost)])
                    res_id = False
                    # Cojo al proveedor
                    partner_obj = self.pool.get('res.partner')
                    partner = partner_obj.browse(cr, uid, supplierinfo_id.name.id)                                        
                    # Fin coger proveedor
                    qty = simulation_cost_line.amount
                    partner_id = partner.id
                    address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                    pricelist_id = partner.property_product_pricelist_purchase.id               
                    warehouse_id = sale_order.shop_id.warehouse_id.id
                    uom_id = simulation_cost_line.uom_id.id
                    price = simulation_cost_line.purchase_price
                    schedule_date = time.strftime('%Y-%m-%d')
                    purchase_date = time.strftime('%Y-%m-%d')
                    context.update({'lang': partner.lang, 'partner_id': partner_id})
                    product = prod_obj.browse(cr, uid, simulation_cost_line.product_id.id, context=context)
                    taxes_ids = simulation_cost_line.product_id.product_tmpl_id.supplier_taxes_id
                    taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
        
                    ###
                    ### Llamo a esta función para validar el subproyecto, y aprovecho
                    ### para imputar en cuenta y en subcuenta analítica, los costes y
                    ### beneficios estimados.
                    ### type=1 es una caso especial, porque la línea de
                    ### pedido de venta no proviene de una simulación de costes,
                    ### por tanto no sé a que pestaña de simulación de costes
                    ### proviene (purchase, investment, subcontracting, others)
                    ### type=2 significa que la línea del pedido de venta
                    ### no proviene de una plantilla de simulacion, y type=3
                    ### significa que la línea de pedido de venta proviene
                    ### de una plantilla de simulación                            
                    w_sale_order_name = sale_order.name
                    w_account_analytic_account_id = account_analytic_account_id
                    w_imp_purchase = simulation_cost_line.subtotal_purchase
                    w_imp_sale = simulation_cost_line.subtotal_sale
                    w_text = simulation_cost_line.type_cost
                    # Si la línea de simulación de coste viene de una línea de plantilla de simulación
                    # le paso su ID
                    w_template_id = simulation_cost_line.template_id.id
                    w_type = 3      
                    # sumo 1 al campo 2_sum_analitic, de esta manera solo imputaré
                    # costes en análitica 1 sola vez.
                    w_sum_analitic = w_sum_analitic + 1
                    #
                    account_id = self._sale_order_purchase_validate_subproject_analytic_account(cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale) 
                    if not purchase_order_id:
                        #
                        ### SI NO EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR
                        line_vals = {'name': simulation_cost_line.name,
                                     'product_qty': qty,
                                     'product_id': simulation_cost_line.product_id.id,
                                     'product_uom': uom_id,
                                     'price_unit': price or 0.0,
                                     'date_planned': time.strftime('%Y-%m-%d'),
                                     'move_dest_id': res_id,
                                     'notes': product.description_purchase,
                                     'taxes_id': [(6,0,taxes)],
                                     }
                        #
                        ### Cojo el tipo de pedido de compra
                        purchase_type_obj = self.pool.get('purchase.type')
                        if simulation_cost_line.type_cost == 'Purchase':
                            purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Purchase')])
                            if not purchase_type_ids:
                                raise osv.except_osv(_('Purchase Order Error'),_('Purchase literal not found in Table Purchase Type'))
                        if simulation_cost_line.type_cost == 'Investment':
                            purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Investment')])
                            if not purchase_type_ids:
                                raise osv.except_osv(_('Purchase Order Error'),_('Invesment literal not found in Table Purchase Type'))
                        if simulation_cost_line.type_cost == 'Subcontracting Services':
                            purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Subcontracting Services')])
                            if not purchase_type_ids:
                                raise osv.except_osv(_('Purchase Order Error'),_('Subcontracting Services literal not found in Table Purchase Type'))
                        if simulation_cost_line.type_cost == 'Task':
                            purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Tasks')])
                            if not purchase_type_ids:
                                raise osv.except_osv(_('Purchase Order Error'),_('Task literal not found in Table Purchase Type'))
                        if simulation_cost_line.type_cost == 'Others':
                            purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Others')])
                            if not purchase_type_ids:
                                raise osv.except_osv(_('Purchase Order Error'),_('Others literal not found in Table Purchase Type'))

                        purchase_type = purchase_type_obj.browse(cr, uid, purchase_type_ids[0])
            
                        ### COJO LA SECUENCIA
                        code = purchase_type.sequence.code
                        name = self.pool.get('ir.sequence').get(cr,uid,code)                                                                  
        
                        po_vals = {'name': name,
                                   'origin': sale_order.name + ' - ' + simulation_cost.simulation_number,
                                   'partner_id': partner_id,
                                   'partner_address_id': address_id,
                                   'location_id': sale_order.shop_id.warehouse_id.lot_stock_id.id,
                                   'warehouse_id': warehouse_id or False,
                                   'pricelist_id': pricelist_id,
                                   'date_order': time.strftime('%Y-%m-%d'),
                                   'company_id': company.id,
                                   'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                                   'type': purchase_type.id,
                                   'type_cost': simulation_cost_line.type_cost
                                   }
                        pc = self._sale_order_create_purchase_order(cr, uid, po_vals, line_vals, context=context)
                        #
                        ### AÑADO EL ID DEL SUBPROYECTO AL PEDIDO DE COMPRA
                        purchase_order_obj.write(cr,uid,[pc],{'sale_order_id': sale_order.id,
                                                              'project3_id': project_project_id})  
                        #
                        ### COJO EL ID DE LA LINEA DE PEDIDO DE COMPRA QUE SE HA DADO DE ALTA    
                        purchase_order_line_obj = self.pool.get('purchase.order.line') 
                        purchase_order_line_ids = purchase_order_line_obj.search(cr, uid,[('order_id','=', pc)])
                        if not purchase_order_line_ids:
                            raise osv.except_osv(_('Purchase Order Creation Error'),_('Purchase Order Line not found(2)'))
                        else:
                            purchase_order_line_id = purchase_order_line_ids[0]     
                        purchaseorder_id = pc
                    else:
                        #
                        ### SI EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR
                        ### DOY DE ALTA UNA LINEA EN LA LINEA DE PEDIDOS DE COMPRA
                        line_vals = {'name': simulation_cost_line.name,
                                     'order_id': purchase_order_id[0],
                                     'product_qty': qty,
                                     'product_id': simulation_cost_line.product_id.id,
                                     'product_uom': uom_id,
                                     'price_unit': price or 0.0,
                                     'date_planned': time.strftime('%Y-%m-%d'),
                                     'move_dest_id': res_id,
                                     'notes': product.description_purchase,
                                     'taxes_id': [(6,0,taxes)],
                                     }   

                        purchase_order_line_obj = self.pool.get('purchase.order.line') 
                        purchase_order_line_id = purchase_order_line_obj.create(cr, uid, line_vals)   
                        purchaseorder_id = purchase_order_id[0]    
          
                    ###
                    ### Llamo a esta función para imputar los costes estimados 
                    ### a la subcuenta analítica expresa de la pestaña de
                    ### simulación de costes de la que proviene.
                    ### Además de imputar los costes estimados, también relacionará
                    ### la línea del pedido de compra, con la subcuenta analítica
                    ### que le corresponde.
                    ### type=1 es una caso especial, porque la línea de
                    ### pedido de venta no proviene de una simulación de costes,
                    ### por tanto no sé a que pestaña de simulación de costes
                    ### proviene (purchase, investment, subcontracting, others)
                    ### type=2 significa que la línea del pedido de venta
                    ### no proviene de una plantilla de simulacion, y type=3
                    ### significa que la línea de pedido de venta proviene
                    ### de una plantilla de simulación
                    w_sale_order_name = sale_order.name
                    w_account_analytic_account_id = account_analytic_account_id
                    w_imp_purchase = simulation_cost_line.subtotal_purchase
                    w_imp_sale = simulation_cost_line.subtotal_sale
                    # Si la línea de simulación de coste viene de una línea de plantilla de simulación
                    w_template_id = simulation_cost_line.template_id.id
                    # En este campo le paso el texto del tipo de coste
                    # (purchase, investment, subcontracting, task, o others)
                    w_text = simulation_cost_line.type_cost
                    w_purchase_order_line_id = purchase_order_line_id
                    w_type = 3

                    subanalytic_account_id = self._sale_order_purchase_validate_subanalytic_account(cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id,w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                    subproject_ids = project_project_obj.search(cr, uid,[('analytic_account_id','=', subanalytic_account_id)])
                    purchase_order_obj.write(cr,uid,[purchaseorder_id],{'project2_id': subproject_ids[0]})         
        return True
    
    def _sale_order_create_purchase_order(self, cr, uid, po_vals, line_vals, context=None):
        if not po_vals.get('type'):
            purchase_type_obj = self.pool.get('purchase.type')
            purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Purchase')])
            if not purchase_type_ids:
                raise osv.except_osv(_('Purchase Order Error'),_('Purchase literal not found in Table Purchase Type'))
            else:
                purchase_type = purchase_type_obj.browse(cr, uid, purchase_type_ids[0])
                po_vals.update({'type':purchase_type.id})

        po_vals.update({'order_line': [(0,0,line_vals)]})

        return self.pool.get('purchase.order').create(cr, uid, po_vals, context=context)
    
    def _sale_order_purchase_validate_subproject_analytic_account(self, cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale):
        #
        ### w_sum_analitic = 1 significa que debe de imputar costos en analítica,
        ### esto lo hacemos porque si un producto viene sin un proveedor en concreto,
        ### realizamos tantos pedidos de compra, como proveedores tenga el producto,
        ### pero solo imputamos en cuentas analíticas 1 vez
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
                raise osv.except_osv(_('Purchase Order Creation Error'),_('Subaccount analytic account not found, literal: ' + w_literal))
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

        if w_sum_analitic == 1:
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
            
        return sub_account_analytic_account_id   
    
    def _sale_order_purchase_validate_subanalytic_account(self, cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale):
        #
        ### w_sum_analitic = 1 significa que debe de imputar costos en analítica,
        ### esto lo hacemos porque si un producto viene sin un proveedor en concreto,
        ### realizamos tantos pedidos de compra, como proveedores tenga el producto,
        ### pero solo imputamos en cuentas analíticas 1 vez
        #
        ### Voy a generar el literal a buscar en subcuenta analítica
        w_literal = ''
        sub_account_analytic_account_id2 = 0
        if w_text == 'Task':
            w_text = 'Internal Task'
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
            raise osv.except_osv(_('Purchase Order Creation Error'),_('Subaccount Analytic Account not found(1), literal: ' + w_literal))

        if w_type == 1:
            # SI LA LINEA DEL PEDIDO DE VENTA NO VIENE DE UNA LINEA DE SIMULACION DE COSTES,
            # NO TENGO MANERA DE ASIGNARLA A NINGUNA PESTAÑA, PERO LO QUE SI SE ES QUE NO
            # ES UNA TAREA INTERNA
            w_literal2 = w_literal + ' (FROM SALE ORDER unknown tab)'
        else:
            # SI LA LINEA DEL PEDIDO DE VENTA VIENE DE UNA LÍNEA DE SIMULACION DE COSTES
            # TENGO QUE BUSCAR LA SUBCUENTA ANALÍTICA QUE LE CORRESPONDA DEPENDIENDO DE LA  
            # PESTAÑA DE LA QUE PROVENGA, ES DECIR... EN LA PANTALLA DE SIMULACIÓN DE COSTES
            # TENEMOS LAS PESTAÑAS: Purchase lines, Investment lines, Subcontractig lines,
            # Task lines, Others lines, PUES TENGO QUE BUSCAR LA SUBCUENTA ANALÍTICA CORRESPONDIENTE
            # A LA SOLAPA DE LA QUE PROVENGA LA LINEA
            #
            # Genero el literal a buscar en Subcuentas Analíticas, en esta búsqueda
            # añado la subcuenta del subproyecto en la búsqueda, porque la subcuenta
            # analítica que tengo que buscar, debe ser una hija del subproyecto
            w_literal2 = w_literal + ' (' + w_text + ')'
            
        sub_account_analytic_account_obj3 = self.pool.get('account.analytic.account')
        sub_account_analytic_account_ids3 = sub_account_analytic_account_obj3.search(cr, uid,[('name','=', w_literal2),
                                                                                              ('parent_id','=', sub_account_analytic_account_id)])
            
        if sub_account_analytic_account_ids3:
            # Si ha encontrado alguna linea, solo habrá encontrado 1,
            # ya que esta buscado una cuenta en concreto, así que me 
            # quedo con su ID
            sub_account_analytic_account_id2 = sub_account_analytic_account_ids3[0]
        else:
            if w_type == 3:
                raise osv.except_osv(_('Purchase Order Creation Error'),_('Subaccount Analytic for tab not found(1), literal: ' + w_literal2))
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
 
        if w_sum_analitic == 1:
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
        #
        # AHORA ACTUALIZO LA LINEA DE PEDIDO DE COMPRA CON SU SUBCUENTA
        # ANALÍTICA CORRESPONDIENTE
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        purchase_order_line_obj.write(cr,uid,[w_purchase_order_line_id],{'account_analytic_id': sub_account_analytic_account_id2})    
            
        return sub_account_analytic_account_id2  
    
    def _generate_project_task(self, cr, uid, sale_order, project_project_id, w_simulation_cost_id, simulation_cost_line, account_analytic_account_id, context=None):
        res = {}
        if context is None:
            context = {}
        project_task = self.pool.get('project.task')
        partner_obj = self.pool.get('res.partner')
        warehouse_obj = self.pool.get('stock.warehouse')
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        w_sale_order_partner_id = sale_order.partner_id.id
        w_sale_order_name = sale_order.name
        w_template_id = simulation_cost_line.template_id.id
        w_account_analytic_account_id = account_analytic_account_id
        w_imp_purchase = simulation_cost_line.subtotal_purchase
        w_imp_sale = simulation_cost_line.subtotal_sale
        w_type = 3
        project_subproject_id = self._sale_order_project_validate_subproject_analytic_account(cr, uid, w_type, w_sale_order_name,  w_sale_order_partner_id, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
        # COJO EL NOMBRE DEL PRODUCTO DE VENTA DE LA LINEA DE SIMULACION DE COSTES
        product_obj = self.pool.get('product.product')
        cost_product = product_obj.browse(cr, uid, simulation_cost_line.product_id.id)
        sale_product = product_obj.browse(cr, uid, simulation_cost_line.product_sale_id.id)
        # DOY DE ALTA LA TAREA PARA EL SUBPROYECTO
        project_task = self.pool.get('project.task')
        task_id = project_task.create(cr, uid, {'name': simulation_cost_line.name,
                                                'date_deadline': time.strftime('%Y-%m-%d'),
                                                'planned_hours': simulation_cost_line.amount,
                                                'remaining_hours': simulation_cost_line.amount,
                                                'user_id': simulation_cost_line.product_id.product_manager.id,
                                                'project_id':  project_subproject_id,
                                                'project3_id': project_project_id,
                                                'company_id': company.id,
                                                'cost_product_name': cost_product.name,
                                                'sale_product_name': sale_product.name,
                                                },context=context)
      
        return True
    
    def _sale_order_project_validate_subproject_analytic_account(self, cr, uid, w_type, w_sale_order_name,  w_sale_order_partner_id, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale):
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
                raise osv.except_osv(_('Purchase Order Creation Error'),_('Subaccount analytic account not found, literal: ' + w_literal))
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
                raise osv.except_osv(_('Purchase Order Creation Error'),_('subproject not found(2), literal: ' + w_literal2))
            else:
                project_subproject_id = project_id[0]       
        else:
            if w_type == 3:
                raise osv.except_osv(_('Purchase Order Creation Error'),_('Subaccount Analytic for tab not found(1), literal: ' + w_literal2))
            else:
                # Doy de alta el subproyecto
                line = {'name' : w_literal,
                        'parent_id': w_account_analytic_account_id,
                        'partner_id':  w_sale_order_partner_id,
                        }
                project_project_obj = self.pool.get('project.project')
                project_subproject_id = project_project_obj.create(cr, uid, line)    
                # Actualizo la subcuenta analitica creada desde el suproyecto
                subproject = project_project_obj.browse(cr, uid, project_subproject_id)
                w_sub_account_analytic_account_id = subproject.analytic_account_id.id
                account_analytic_account_obj.write(cr,uid,[w_sub_account_analytic_account_id],{'name' : w_literal,
                                                                                               'type': 'normal',
                                                                                               'state': 'open',
                                                                                               'estimated_balance': 0,
                                                                                               'estimated_cost': 0,
                                                                                               'estimated_sale': 0,
                                                                              })                  
                line = {'name' : w_literal2,
                        'parent_id':  w_sub_account_analytic_account_id,
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

sale_order()
