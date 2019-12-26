# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields
# from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
# from tools.translate import _

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
### HEREDO ESTA CLASE PARA MODIFICAR EL TRATAMIENTO DE CREAR PEDIDOS DE COMPRA,
### CUANDO EL PEDIDO DE VENTA HA SIDO GENERADO DESDE UNA SIMULACIÓN DE COSTE


class ProcurementOrder(models.Model):
    _name = 'procurement.order'
    _inherit = 'procurement.order'
    
    message = fields.Char(
        string='Latest error',
        size=164,
        help="Exception occurred while computing procurement orders.")

    def make_po(self, cr, uid, ids, context=None):
        
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
        project_project_obj = self.pool.get('project.project')
        
        for procurement in self.browse(cr, uid, ids, context=context):
            if procurement.product_id.type == 'service' and procurement.product_id.procure_method =='make_to_stock':
                res[procurement.id] = False
                continue
            if procurement.sale_line_id:
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
                ### ACTIVA QUE NO ESTE CANCELADA, O LA ÚLTIMA HISTORIFICADA
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
                            # Si no he encontrado una simulación de coste historificada para eses pedido de venta
                            raise osv.except_osv(_('Purchase Order Creation Error'),_('Simulation Cost not found'))
                        else:
                            #Si no he encontrado una simulación de coste activa para ese pedido de venta,
                            # me quedo con el id de la simulación de coste historificada mas nueva
                            w_simulation_cost_id = w_maxid
                            
                    #
                    ### ACCEDO AL OBJETO SIMULACION
                    simulation_cost_obj = self.pool.get('simulation.cost') 
                    simulation_cost = simulation_cost_obj.browse(cr, uid, w_simulation_cost_id)

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
                                res[procurement.id] = False
                                continue       
      
            #
            ### Si EL PEDIDO DE VENTA VIENE DE UNA SIMULACIÓN, MIRO SI YA TIENE ASOCIADO
            ### UN PROYECTO
            if procurement.sale_line_id:
                if sale_order.simulation_cost_ids:              
                    if not sale_order.project2_id:
                        raise osv.except_osv(_('Purchase Order Creation Error'),_('Project not found'))
                    else:                    
                        #SI EL PEDIDO DE VENTA TIENE UN PROYECTO ASOCIADO, COJO SU ID 
                        project_project_id = sale_order.project2_id.id
                        # Ahora cojo su cuenta analítica
                         
                        project_project = project_project_obj.browse(cr, uid,  project_project_id)
                        account_analytic_account_id = project_project.analytic_account_id.id                
                       
            #
            ### SI EL PEDIDO DE VENTA NO VIENE DE UNA SIMULACION, HAGO EL TRATAMIENTO DE ANTES
            if not procurement.sale_line_id:
                #
                ### Llamo con SUPER al método padre
                res = super(procurement_order, self).make_po(cr, uid, [procurement.id], context=None) 
                purchase_order_id = res[procurement.id]
                purchase_order = purchase_order_obj.browse(cr,uid, purchase_order_id)
                type_o=self.pool.get('purchase.type').browse(cr,uid,purchase_order.type.id)  
                code = type_o.sequence.code
                seq = self.pool.get('ir.sequence').get(cr,uid,code)                 
                purchase_order_obj.write(cr, uid, [purchase_order_id],{'name': seq})
            else:
                if not sale_order.simulation_cost_ids:
                    #
                    ### Llamo con SUPER al método padre
                    res = super(procurement_order, self).make_po(cr, uid, [procurement.id], context=None)  
                    purchase_order_id = res[procurement.id]               
                    purchase_order = purchase_order_obj.browse(cr,uid, purchase_order_id)
                    type_o=self.pool.get('purchase.type').browse(cr,uid,purchase_order.type.id)  
                    code = type_o.sequence.code
                    seq = self.pool.get('ir.sequence').get(cr,uid,code)                 
                    purchase_order_obj.write(cr, uid, [purchase_order_id],{'name': seq})
                else:    
                    ### SI EL PEDIDO DE VENTA VIENE DE UNA SIMULACION
                    if not sale_order_line.simulation_cost_line_ids:
                        #
                        ### SI LA LINEA DEL PEDIDO DE VENTA NO VIENE DE UNA LINEA
                        ### DE SIMULACION DE COSTE
                        if procurement.product_id.seller_id:
                            ### SI EL PRODUCTO VIENE CON UN PROVEEDOR EN CONCRETO, TRATO ESE PROVEEDOR           
                            ###
                            ### MIRO SI YA EXISTE UN PEDIDO DE COMPRA PARA ESTE PROVEEDOR QUE VIENE 
                            ### EN LA LÍNEA
                            purchase_order_obj = self.pool.get('purchase.order')
                            purchase_order_id = purchase_order_obj.search(cr, uid,[('sale_order_id','=', sale_order.id),
                                                                                   ('partner_id', '=', procurement.product_id.seller_id.id), 
                                                                                   ('state', '=', 'draft'),                                                                                                                                         
                                                                                   ('type_cost','=', 'Purchase')])
                            res_id = procurement.move_id.id
                            partner = procurement.product_id.seller_id 
                            seller_qty = procurement.product_id.seller_qty
                            partner_id = partner.id
                            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                            pricelist_id = partner.property_product_pricelist_purchase.id
                            warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
                            uom_id = procurement.product_id.uom_po_id.id
                            qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
                            if seller_qty:
                                qty = max(qty,seller_qty)
                            price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]            
    
                            product_obj = self.pool.get('product.product')
                            product = product_obj.browse(cr, uid, procurement.product_id.id)                    
                             
                            ###
                            ### Llamo a esta función para validar el subproyecto, y aprovecho
                            ### para imputar en cuenta y eb subcuenta analítica, los costes y
                            ### beneficios estimados, parámetro type=1 significa que la línea
                            ### del pedido de venta no viene de simulación de costes                    
                            w_sale_order_name = sale_order.name
                            w_template_id = 0
                            w_account_analytic_account_id = account_analytic_account_id
                            w_imp_purchase = qty * price
                            w_imp_sale = qty * product.list_price
                            # Al venir el producto con un proveedor en concreto, sumo el importe
                            # de coste a analítica, eso lo indico poniento w_sum_analitic = 1
                            w_sum_analitic = 1
                            # w_type = 1 indica que la línea de pedido de venta no viene de una
                            # línea de simulación de coste.
                            w_type = 1
                            account_id = self._purchase_validate_subproject_analytic_account(cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                            if not purchase_order_id:
                                #
                                ### Si NO EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR,
                                ### LLAMO AL MÉTODO PADRE PARA REALIZAR EL MISMO TRATAMIENTO
                                res = super(procurement_order, self).make_po(cr, uid, [procurement.id], context=None)
                                #
                                ### COJO LA SECUENCIA
                                purchase_type_obj = self.pool.get('purchase.type')
                                purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Purchase')])
                                purchase_type = purchase_type_obj.browse(cr, uid, purchase_type_ids[0])
                                code = purchase_type.sequence.code
                                seq = self.pool.get('ir.sequence').get(cr,uid,code)
                                #
                                ### MODIFICO EL PEDIDO DE COMPRA AÑADIENDOLE EL CODIGO DE PEDIDO DE VENTA, EL PROYECTO, Y EL TIPO DE COMPRA
                                pc=res[procurement.id]  
                                purchase_order_obj.write(cr,uid,[pc],{'name': seq,
                                                                      'sale_order_id': sale_order.id,
                                                                      'project3_id': project_project_id,
                                                                      'origin': procurement.origin + ' - ' + simulation_cost.simulation_number,
                                                                      'type_cost': 'Purchase'}) 
                                #
                                ### COJO EL ID DE LA LINEA DE PEDIDO DE COMPRA QUE SE HA DADO DE ALTA    
                                purchase_order_line_obj = self.pool.get('purchase.order.line') 
                                purchase_order_line_ids = purchase_order_line_obj.search(cr, uid,[('order_id','=', pc)])
                                if not purchase_order_line_ids:
                                    raise osv.except_osv(_('Purchase Order Creation Error'),_('Purchase Order Line not found(1)'))
                                else:
                                    purchase_order_line_id = purchase_order_line_ids[0] 
                                purchaseorder_id = pc
                            else:
                                #
                                ### Si EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR,
                                ### DOY DE ALTA UNA LINEA EN LA LINEA DE PEDIDOS DE COMPRA
                                res_id = procurement.move_id.id
                                partner = procurement.product_id.seller_id # Taken Main Supplier of Product of Procurement.
                                seller_qty = procurement.product_id.seller_qty
                                partner_id = partner.id
                                address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                                pricelist_id = partner.property_product_pricelist_purchase.id
                                warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
                                uom_id = procurement.product_id.uom_po_id.id
    
                                qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
                                if seller_qty:
                                    qty = max(qty,seller_qty)
    
                                price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]
    
                                schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
                                purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)
    
                                #Passing partner_id to context for purchase order line integrity of Line name
                                context.update({'lang': partner.lang, 'partner_id': partner_id})
    
                                product = prod_obj.browse(cr, uid, procurement.product_id.id, context=context)
                                taxes_ids = procurement.product_id.product_tmpl_id.supplier_taxes_id
                                taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
          
                                line_vals = {'order_id' : purchase_order_id[0],
                                             'name': product.partner_ref,
                                             'product_qty': qty,
                                             'product_id': procurement.product_id.id,
                                             'product_uom': uom_id,
                                             'price_unit': price or 0.0,
                                             'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
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
                            ### de una plantilla de simulación.
                            w_template_id = 0
                            w_text = ''
                            w_purchase_order_line_id = purchase_order_line_id
                            # Al venir el producto con un proveedor en concreto, sumo el importe
                            # de coste a analítica, eso lo indico poniento w_sum_analitic = 1
                            w_sum_analitic = 1
                            # w_type = 1 indica que la línea de pedido de venta no viene de una
                            # línea de simulación de coste.
                            w_type = 1 
                            subanalytic_account_id = self._purchase_validate_subanalytic_account(cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id,w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                            subproject_ids = project_project_obj.search(cr, uid,[('analytic_account_id','=', subanalytic_account_id)])
                            purchase_order_obj.write(cr,uid,[purchaseorder_id],{'project2_id': subproject_ids[0]}) 
                        else:
                            ### SI EL PRODUCTO NO VIENE CON UN PROVEEDOR EN CONCRETO, TRATO TODOS SUS PROVEEDORES    
                            supplierinfo_obj = self.pool.get('product.supplierinfo')
                            supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', product.id)]) 
                            if not supplierinfo_ids:
                                # Si no hay proveedores definidos para el producto, muestro el error
                                raise osv.except_osv(_('Purchase Order Creation Error'),_('You must define one supplier for the product: ' + product.name))
                            else:
                                # TRATO TODOS LOS PROVEEDORES ENCONTRADOS PARA EL PRODUCTO,
                                # CREARE UN PEDIDO DE COMPRA PARA CADA PROVEEDOR DE ESE
                                # PRODUCTO
                                # Como el producto no viene con un proveedor en concreto, debo de grabar
                                # un pedido de compra por cada proveedor, es por ello que inicializo el 
                                # campo w_sum_analitic a 0, e iré sumando 1 a este campo por cada proveedor
                                # que trate de ese producto, de esta manera solo imputaré a cuentas analíticas
                                # 1 única vez
                                w_sum_analitic = 0
                                #
                                for supplierinfo_id in supplierinfo_ids:
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
                                                                                           ('type_cost','=', 'Purchase')])
                                    res_id = procurement.move_id.id
                                    # Cojo al proveedor
                                    partner_obj = self.pool.get('res.partner')
                                    partner = partner_obj.browse(cr, uid, supplierinfo_id.name.id)                                        
                                    # Fin coger proveedor                                
                                    seller_qty = procurement.product_id.seller_qty
                                    partner_id = partner_id.id
                                    address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                                    pricelist_id = partner.property_product_pricelist_purchase.id
                                    warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
                                    uom_id = procurement.product_id.uom_po_id.id
                                    qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
                                    if seller_qty:
                                        qty = max(qty,seller_qty)
                                    price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]            
    
                                    product_obj = self.pool.get('product.product')
                                    product = product_obj.browse(cr, uid, procurement.product_id.id)                    
                             
                                    ###
                                    ### Llamo a esta función para validar el subproyecto, y aprovecho
                                    ### para imputar en cuenta y eb subcuenta analítica, los costes y
                                    ### beneficios estimados, parámetro type=1 significa que la línea
                                    ### del pedido de venta no viene de simulación de costes                    
                                    w_sale_order_name = sale_order.name
                                    w_template_id = 0
                                    w_account_analytic_account_id = account_analytic_account_id
                                    w_imp_purchase = qty * price
                                    w_imp_sale = qty * product.list_price
                                    # sumo 1 al campo 2_sum_analitic, de esta manera solo imputaré
                                    # costes en análitica 1 sola vez.
                                    w_sum_analitic = w_sum_analitic + 1
                                    # w_type = 1 indica que la línea de pedido de venta no viene de una
                                    # línea de simulación de coste.
                                    w_type = 1
                                    account_id = self._purchase_validate_subproject_analytic_account(cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                                    if not purchase_order_id:
                                        #
                                        ### Si NO EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR,
                                        ### LLAMO AL MÉTODO PADRE PARA REALIZAR EL MISMO TRATAMIENTO
                                        res = super(procurement_order, self).make_po(cr, uid, [procurement.id], context=None)
                                        ### COJO LA SECUENCIA
                                        purchase_type_obj = self.pool.get('purchase.type')
                                        purchase_type_ids = purchase_type_obj.search(cr, uid,[ ('name','=', 'Purchase')])
                                        purchase_type = purchase_type_obj.browse(cr, uid, purchase_type_ids[0])
                                        code = purchase_type.sequence.code
                                        seq = self.pool.get('ir.sequence').get(cr,uid,code)
                                        #
                                        ### MODIFICO EL PEDIDO DE COMPRA AÑADIENDOLE EL CODIGO DE PROVEEDOR, EL CODIGO DE PEDIDO DE VENTA, EL PROYECTO, Y EL TIPO DE COMPRA
                                        pc=res[procurement.id]  
                                        purchase_order_obj.write(cr,uid,[pc],{'name': seq,
                                                                              'partner_id': partner_id,
                                                                              'sale_order_id': sale_order.id,
                                                                              'project3_id': project_project_id,
                                                                              'origin': procurement.origin + ' - ' + simulation_cost.simulation_number,
                                                                              'type_cost': 'Purchase'}) 
                                        #
                                        ### COJO EL ID DE LA LINEA DE PEDIDO DE COMPRA QUE SE HA DADO DE ALTA    
                                        purchase_order_line_obj = self.pool.get('purchase.order.line') 
                                        purchase_order_line_ids = purchase_order_line_obj.search(cr, uid,[('order_id','=', pc)])
                                        if not purchase_order_line_ids:
                                            raise osv.except_osv(_('Purchase Order Creation Error'),_('Purchase Order Line not found(1)'))
                                        else:
                                            purchase_order_line_id = purchase_order_line_ids[0] 
                                        purchaseorder_id = pc
                                    else:
                                        #
                                        ### Si EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR,
                                        ### DOY DE ALTA UNA LINEA EN LA LINEA DE PEDIDOS DE COMPRA
                                        res_id = procurement.move_id.id
                                        partner = partner.obj.browse(cr, uid, supplierinfo_id)
                                        seller_qty = procurement.product_id.seller_qty
                                        partner_id = partner.id
                                        address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                                        pricelist_id = partner.property_product_pricelist_purchase.id
                                        warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
                                        uom_id = procurement.product_id.uom_po_id.id
    
                                        qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
                                        if seller_qty:
                                            qty = max(qty,seller_qty)
    
                                        price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]
    
                                        schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
                                        purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)
    
                                        #Passing partner_id to context for purchase order line integrity of Line name
                                        context.update({'lang': partner.lang, 'partner_id': partner_id})
    
                                        product = prod_obj.browse(cr, uid, procurement.product_id.id, context=context)
                                        taxes_ids = procurement.product_id.product_tmpl_id.supplier_taxes_id
                                        taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
          
                                        line_vals = {'order_id' : purchase_order_id[0],
                                                     'name': product.partner_ref,
                                                     'product_qty': qty,
                                                     'product_id': procurement.product_id.id,
                                                     'product_uom': uom_id,
                                                     'price_unit': price or 0.0,
                                                     'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
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
                                    ### de una plantilla de simulación.
                                    w_template_id = 0
                                    w_text = ''
                                    w_purchase_order_line_id = purchase_order_line_id
                                    w_type = 1 
                                    subanalytic_account_id = self._purchase_validate_subanalytic_account(cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id,w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                                    subproject_ids = project_project_obj.search(cr, uid,[('analytic_account_id','=', subanalytic_account_id)])
                                    purchase_order_obj.write(cr,uid,[purchaseorder_id],{'project2_id': subproject_ids[0]}) 

                    else:
                        ### SI LA LINEA DEL PEDIDO DE VENTA, VIENE DE UNA LINEA DE
                        ### SIMULACIÓN DE COSTE, TRATO TODAS LA LINEAS DE SIMULACION DE COSTE
                        for simulation_cost_line in  sale_order_line.simulation_cost_line_ids:
                            # Si la linea de simulación de coste, se corresponde con la linea
                            # de simulación de coste perteneciente a la simulación de coste activa
                            # o a la última historificada, trato la linea.
                            if simulation_cost_line.simulation_cost_id.id == w_simulation_cost_id:
                                
                                
                                
                                
                                
                                if simulation_cost_line.supplier_id:
                                    ### SI EL PRODUCTO VIENE CON UN PROVEEDOR EN CONTRETO, TRATO ESE PROVEEDOR 
                                    #
                                    ### MIRO SI YA EXISTE UN PEDIDO DE COMPRA PARA ESTE PROVEEDOR QUE VIENE 
                                    ### EN LA LÍNEA
                                    purchase_order_obj = self.pool.get('purchase.order')
                                    purchase_order_id = purchase_order_obj.search(cr, uid,[('sale_order_id','=', sale_order.id),
                                                                                           ('partner_id', '=', simulation_cost_line.supplier_id.id),
                                                                                           ('state', '=', 'draft'),     
                                                                                           ('type_cost','=', simulation_cost_line.type_cost)])
                                    res_id = procurement.move_id.id
                                    partner = simulation_cost_line.supplier_id
                                    qty = simulation_cost_line.amount
                                    partner_id = partner.id
                                    address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                                    pricelist_id = partner.property_product_pricelist_purchase.id
                                    warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
                                    uom_id = simulation_cost_line.uom_id.id
                                    price = simulation_cost_line.purchase_price
                                    schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
                                    purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)
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
                                    if not simulation_cost_line.template_id:
                                        #raise osv.except_osv('Purchase Order Creation Error', 'Product: ' +  product.name + 'without Simulation Template')
                                        # Si la linea de simulación de coste no viene de una línea de plantilla de simulación
                                        w_template_id = 0
                                        w_type = 2
                                    else:
                                        # Si la línea de simulación de coste viene de una línea de plantilla de simulación
                                        # le paso su ID
                                        w_template_id = simulation_cost_line.template_id.id
                                        w_type = 3
    
                                    # Al venir el producto con un proveedor en concreto, sumo el importe
                                    # de coste a analítica, eso lo indico poniento w_sum_analitic = 1
                                    w_sum_analitic = 1
                                    #
                                    account_id = self._purchase_validate_subproject_analytic_account(cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)                      
                                    if not purchase_order_id:
                                        #
                                        ### SI NO EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR
                                        line_vals = {'name': simulation_cost_line.name,
                                                     'product_qty': qty,
                                                     'product_id': simulation_cost_line.product_id.id,
                                                     'product_uom': uom_id,
                                                     'price_unit': price or 0.0,
                                                     'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
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
                                                   'origin': procurement.origin + ' - ' + simulation_cost.simulation_number,
                                                   'partner_id': partner_id,
                                                   'partner_address_id': address_id,
                                                   'location_id': procurement.location_id.id,
                                                   'warehouse_id': warehouse_id and warehouse_id[0] or False,
                                                   'pricelist_id': pricelist_id,
                                                   'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                   'company_id': procurement.company_id.id,
                                                   'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                                                   'type': purchase_type.id,
                                                   'type_cost': simulation_cost_line.type_cost
                                                   }
                                        res[procurement.id] = self.create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=context)
                                        self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': res[procurement.id]})
                                        #
                                        ### AÑADO EL ID DEL SUBPROYECTO AL PEDIDO DE COMPRA
                                        pc=res[procurement.id]
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
                                                     'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
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
                                    if not simulation_cost_line.template_id:
                                        # Si la linea de simulación de coste no viene de una línea de plantilla de simulación            
                                        w_template_id = 0
                                        # En este campo le paso el texto del tipo de coste
                                        # (purchase, investment, subcontracting, task, o others)
                                        w_text = simulation_cost_line.type_cost
                                        w_purchase_order_line_id = purchase_order_line_id
                                        w_type = 2
                                    else:
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
                                    subanalytic_account_id = self._purchase_validate_subanalytic_account(cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id,w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
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
                                            res_id = procurement.move_id.id
                                            # Cojo al proveedor
                                            partner_obj = self.pool.get('res.partner')
                                            partner = partner_obj.browse(cr, uid, supplierinfo_id.name.id)                                        
                                            # Fin coger proveedor
                                            qty = simulation_cost_line.amount
                                            partner_id = partner.id
                                            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                                            pricelist_id = partner.property_product_pricelist_purchase.id
                                            warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
                                            uom_id = simulation_cost_line.uom_id.id
                                            price = simulation_cost_line.purchase_price
                                            schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
                                            purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)
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
                                            if not simulation_cost_line.template_id:
                                                product_obj = self.pool.get('product.product')
                                                cost_product = product_obj.browse(cr, uid, simulation_cost_line.product_id.id)
                                                #raise osv.except_osv('Purchase Order Creation Error', 'Product: ' +  product.name + 'without Simulation Template')
                                                # Si la linea de simulación de coste no viene de una línea de plantilla de simulación
                                                w_template_id = 0
                                                w_type = 2
                                            else:
                                                # Si la línea de simulación de coste viene de una línea de plantilla de simulación
                                                # le paso su ID
                                                w_template_id = simulation_cost_line.template_id.id
                                                w_type = 3
                                                
                                            # sumo 1 al campo 2_sum_analitic, de esta manera solo imputaré
                                            # costes en análitica 1 sola vez.
                                            w_sum_analitic = w_sum_analitic + 1
                                            #
                                            account_id = self._purchase_validate_subproject_analytic_account(cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                                            #
                                            if not purchase_order_id:
                                                #
                                                ### SI NO EXISTE EL PEDIDO DE COMPRA PARA EL PROVEEDOR
                                                line_vals = {'name': simulation_cost_line.name,
                                                             'product_qty': qty,
                                                             'product_id': simulation_cost_line.product_id.id,
                                                             'product_uom': uom_id,
                                                             'price_unit': price or 0.0,
                                                             'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
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
                                                           'origin': procurement.origin + ' - ' + simulation_cost.simulation_number,
                                                           'partner_id': partner_id,
                                                           'partner_address_id': address_id,
                                                           'location_id': procurement.location_id.id,
                                                           'warehouse_id': warehouse_id and warehouse_id[0] or False,
                                                           'pricelist_id': pricelist_id,
                                                           'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                           'company_id': procurement.company_id.id,
                                                           'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                                                           'type': purchase_type.id,
                                                           'type_cost': simulation_cost_line.type_cost
                                                           }
                                                res[procurement.id] = self.create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=context)
                                                self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': res[procurement.id]})
                                                #
                                                ### AÑADO EL ID DEL SUBPROYECTO AL PEDIDO DE COMPRA
                                                pc=res[procurement.id]
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
                                                             'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
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
                                            if not simulation_cost_line.template_id:
                                                # Si la linea de simulación de coste no viene de una línea de plantilla de simulación            
                                                w_template_id = 0
                                                # En este campo le paso el texto del tipo de coste
                                                # (purchase, investment, subcontracting, task, o others)
                                                w_text = simulation_cost_line.type_cost
                                                w_purchase_order_line_id = purchase_order_line_id
                                                w_type = 2
                                            else:
                                                # Si la línea de simulación de coste viene de una línea de plantilla de simulación
                                                w_template_id = simulation_cost_line.template_id.id
                                                # En este campo le paso el texto del tipo de coste
                                                # (purchase, investment, subcontracting, task, o others)
                                                w_text = simulation_cost_line.type_cost
                                                w_purchase_order_line_id = purchase_order_line_id
                                                w_type = 3
    
                                            subanalytic_account_id = self._purchase_validate_subanalytic_account(cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id,w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale)
                                            subproject_ids = project_project_obj.search(cr, uid,[('analytic_account_id','=', subanalytic_account_id)])
                                            purchase_order_obj.write(cr,uid,[purchaseorder_id],{'project2_id': subproject_ids[0]}) 

        return res
    
    #
    ## HEREDO ESTA FUNCION QUE CREA LA ORDEN DE PEDIDO DE COMPRA
    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals, line_vals, context=None):
        
        """Create the purchase order from the procurement, using
           the provided field values, after adding the given purchase
           order line in the purchase order.

           :params procurement: the procurement object generating the purchase order
           :params dict po_vals: field values for the new purchase order (the
                                 ``order_line`` field will be overwritten with one
                                 single line, as passed in ``line_vals``).
           :params dict line_vals: field values of the single purchase order line that
                                   the purchase order will contain.
           :return: id of the newly created purchase order
           :rtype: int
        """
        #
        ### MODIFICACION: Si no viene un parametro con nombre 'type',
        ### significa que no viene de una simulación, por lo tanto lo
        ### ponemos el campo "type" como de compras (este campo indica
        ### que tipo de de pedido de compra es, y servirá para generar
        ### el código del pedido de compra
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

    #
    ### Funcion para validar que existe la subcuenta analitica,
    ### si no existe la subcuenta analitica la crea, y tambien
    ### crea su subproyecto.
    ### En esta funcion tambien se realiza la imputacion de la
    ### estimacion de costes y beneficios en la subcuenta analitica
    def _purchase_validate_subproject_analytic_account(self, cr, uid, w_sum_analitic, w_type, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale):
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

    def _purchase_validate_subanalytic_account(self, cr, uid, w_sum_analitic, w_type, w_text, w_purchase_order_line_id, w_sale_order_name, w_simulation_cost_id, w_template_id, w_account_analytic_account_id, w_imp_purchase, w_imp_sale):
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


procurement_order()
