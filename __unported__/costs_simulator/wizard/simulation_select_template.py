# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class SimulationSelectTemplate(models.TransientModel):
    _name = 'simulation.select.template'
    _description = "Wizard Select Template"
 
    template_id = fields.Many2one(
        comodel_name='simulation.template',
        string='Template')

    def view_init(self, cr, uid, ids, context=None):
        
        simu_id = context.get('active_id')
        ### Valido que la simulación del coste no este historificada
        ### Leo el Objeto Coste
        simulation_cost_obj = self.pool.get('simulation.cost')
        simulation_cost = simulation_cost_obj.browse(cr, uid, simu_id)
        ### valido que no esté historificado ya
        if simulation_cost.historical_date:
            raise exceptions.Warning(
                _('Error'),
                _('This cost simulation have Historical'))
    ### Función
    def template_selected(self, cr, uid, ids, context=None):
        #
        ### debo de cerrar el wizard de la siguiente manera
        #
        res={}
        
        cost_line_obj = self.pool.get('simulation.cost.line')
        
        simu_id = context.get('active_id')
        
        for wiz in self.browse(cr,uid,ids,context):
            src_temp = wiz.template_id
            data={}
            
            for line1 in src_temp.purchase_template_lines_ids:
                ### Cojo datos del producto
                product_obj = self.pool.get('product.product')
                product = product_obj.browse(cr, uid, line1.product_id.id)
                ### Cojo el primer proveedor para el producto
                supplierinfo_obj = self.pool.get('product.supplierinfo')
                supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', line1.product_id.id)],                                                                 
                                                                    order='sequence')
                ### Si no tiene cantidad, le pongo 1
                if not line1.amount:
                    line1.amount = 1.0
                ### Diferencio si el producto tiene proveedores o no tiene
                if supplierinfo_ids:
                    supplierinfo_id = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0])
                    partner = self.pool.get('res.partner')
                    supplier = partner.browse(cr, uid, supplierinfo_id.name.id)
                    lang = partner.browse(cr, uid, supplierinfo_id.name.id).lang
                    pricelist_id = supplier.property_product_pricelist_purchase.id
                    ### Accedo a datos del producto.
                    product_product = self.pool.get('product.product')
                    context_partner = {'lang': lang, 'partner_id': supplierinfo_id.name.id}
                    product = product_product.browse(cr, uid, line1.product_id.id, context=context_partner)                
                    ### Le pongo la fecha del sistema
                    estimated_date_purchase_completion = fields.Date.context_today
                    ### Cojo el precio de compra según tablas.
                    product_pricelist = self.pool.get('product.pricelist')
                    price = product_pricelist.price_get(cr, uid, [pricelist_id], product.id, line1.amount, supplierinfo_id.name.id, {'uom': product.uom_id.id, 'date': estimated_date_purchase_completion})[pricelist_id]                       
                    ### Calculo el total compra
                    subtotal_purchase = line1.amount * price     
                    # Calculo el margen estimado
                    if line1.product_id.list_price > 0 and price > 0:
                        estimated_margin = (line1.product_id.list_price / price)-1    
                    else:
                        estimated_margin = 0       
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line1.product_id.id,
                        'product_sale_id': line1.product_id.id,
                        'name': line1.name,
                        'description': line1.description,
                        'supplier_id': supplierinfo_id.name.id,
                        'purchase_price': price,
                        'sale_price': line1.product_id.list_price,
                        'uom_id': line1.uom_id.id,
                        'amount': line1.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'amortization_rate': 0,
                        'amortization_cost': 0,
                        'indirect_cost_rate': 0,
                        'indirect_cost': 0,
                        'type_cost': line1.type_cost,
                        'type2': line1.type2,
                        'type3': line1.type3,
                        'template_id': src_temp.id,
                        'estimated_date_purchase_completion': estimated_date_purchase_completion,
                        'estimated_margin': estimated_margin
                    }
                    cost_line_obj.create(cr,uid,data)
                else:
                    ### Calculo el total de la venta
                    if product.standard_price:
                        subtotal_purchase = line1.amount * product.standard_price
                    else:
                        subtotal_purchase = 0
                    # Calculo el margen estimado
                    if line1.product_id.list_price > 0 and product.standard_price > 0:
                        estimated_margin = (line1.product_id.list_price / product.standard_price)-1    
                    else:
                        estimated_margin = 0                           
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line1.product_id.id,
                        'product_sale_id': line1.product_id.id,
                        'name': line1.name,
                        'description': line1.description,
                        'purchase_price': product.standard_price,
                        'sale_price': line1.product_id.list_price,
                        'amortization_rate': 0,
                        'amortization_cost': 0,
                        'indirect_cost_rate': 0,
                        'indirect_cost': 0,
                        'uom_id': line1.uom_id.id,
                        'amount': line1.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'type_cost': line1.type_cost,
                        'type2': line1.type2,
                        'type3': line1.type3,
                        'template_id': src_temp.id,
                        'estimated_margin': estimated_margin }
                    cost_line_obj.create(cr, uid, data)
            for line2 in src_temp.investment_template_lines_ids:
                ### Cojo datos del producto
                product_obj = self.pool.get('product.product')
                product = product_obj.browse(cr, uid, line2.product_id.id)
                ### Cojo el primer proveedor para el producto
                supplierinfo_obj = self.pool.get('product.supplierinfo')
                supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', line2.product_id.id)],                                                                 
                                                                    order='sequence')
                ### Si no tiene cantidad, le pongo 1
                if not line2.amount:
                    line2.amount = 1.0
                ### Diferencio si el producto tiene proveedores o no tiene
                if supplierinfo_ids:
                    supplierinfo_id = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0])
                    partner = self.pool.get('res.partner')
                    supplier = partner.browse(cr, uid, supplierinfo_id.name.id)
                    lang = partner.browse(cr, uid, supplierinfo_id.name.id).lang
                    pricelist_id = supplier.property_product_pricelist_purchase.id
                    ### Accedo a datos del producto.
                    product_product = self.pool.get('product.product')
                    context_partner = {'lang': lang, 'partner_id': supplierinfo_id.name.id}
                    product = product_product.browse(cr, uid, line2.product_id.id, context=context_partner)                
                    ### Le pongo la fecha del sistema
                    estimated_date_purchase_completion = time.strftime('%Y-%m-%d')          
                    ### Cojo el precio de compra según tablas.
                    product_pricelist = self.pool.get('product.pricelist')
                    price = product_pricelist.price_get(cr, uid, [pricelist_id], product.id, line2.amount, supplierinfo_id.name.id, {'uom': product.uom_id.id, 'date': estimated_date_purchase_completion})[pricelist_id]                       
                    ### Calculo el total compra
                    subtotal_purchase = line2.amount * price          
                    # Calculo el margen estimado
                    if line2.product_id.list_price > 0 and price > 0:
                        estimated_margin = (line2.product_id.list_price / price)-1    
                    else:
                        estimated_margin = 0             
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line2.product_id.id,
                        'product_sale_id': line2.product_id.id,
                        'name': line2.name,
                        'description': line2.description,
                        'supplier_id': supplierinfo_id.name.id,
                        'purchase_price': price,
                        'sale_price': line2.product_id.list_price,
                        'uom_id': line2.uom_id.id,
                        'amount': line2.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'amortization_rate': 0,
                        'amortization_cost': 0,
                        'indirect_cost_rate': 0,
                        'indirect_cost': 0,
                        'type_cost': line2.type_cost,
                        'type2': line2.type2,
                        'type3': line2.type3,
                        'template_id': src_temp.id,
                        'estimated_date_purchase_completion': estimated_date_purchase_completion,
                        'estimated_margin': estimated_margin
                    }
                    cost_line_obj.create(cr, uid, data)
                else:
                    ### Calculo el total de la venta
                    if product.standard_price:
                        subtotal_purchase = line2.amount * product.standard_price
                    else:
                        subtotal_purchase = 0
                    # Calculo el margen estimado
                    if line2.product_id.list_price > 0 and product.standard_price > 0:
                        estimated_margin = (line2.product_id.list_price / product.standard_price)-1    
                    else:
                        estimated_margin = 0    
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line2.product_id.id,
                        'product_sale_id': line2.product_id.id,
                        'name': line2.name,
                        'description': line2.description,
                        'purchase_price': product.standard_price,
                        'sale_price': line2.product_id.list_price,
                        'uom_id': line2.uom_id.id,
                        'amount': line2.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'amortization_rate': 0,
                        'amortization_cost': 0,
                        'indirect_cost_rate': 0,
                        'indirect_cost': 0,
                        'type_cost': line2.type_cost,
                        'type2': line2.type2,
                        'type3': line2.type3,
                        'template_id': src_temp.id,
                        'estimated_margin': estimated_margin }
                    cost_line_obj.create(data)

            for line3 in src_temp.subcontracting_template_lines_ids:
                ### Cojo datos del producto
                product_obj = self.pool.get('product.product')
                product = product_obj.browse(cr, uid, line3.product_id.id)
                ### Cojo el primer proveedor para el producto
                supplierinfo_obj = self.pool.get('product.supplierinfo')
                supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', line3.product_id.id)],                                                                 
                                                                    order='sequence')
                ### Si no tiene cantidad, le pongo 1
                if not line3.amount:
                    line3.amount = 1.0
                ### Diferencio si el producto tiene proveedores o no tiene
                if supplierinfo_ids:
                    supplierinfo_id = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0])
                    partner = self.pool.get('res.partner')
                    supplier = partner.browse(cr, uid, supplierinfo_id.name.id)
                    lang = partner.browse(cr, uid, supplierinfo_id.name.id).lang
                    pricelist_id = supplier.property_product_pricelist_purchase.id
                    ### Accedo a datos del producto.
                    product_product = self.pool.get('product.product')
                    context_partner = {'lang': lang, 'partner_id': supplierinfo_id.name.id}
                    product = product_product.browse(cr, uid, line3.product_id.id, context=context_partner)                
                    ### Le pongo la fecha del sistema
                    estimated_date_purchase_completion = fields.Date.context_today
                    ### Cojo el precio de compra según tablas.
                    product_pricelist = self.pool.get('product.pricelist')
                    price = product_pricelist.price_get(cr, uid, [pricelist_id], product.id, line3.amount, supplierinfo_id.name.id, {'uom': product.uom_id.id, 'date': estimated_date_purchase_completion})[pricelist_id]                       
                    ### Calculo el total compra
                    subtotal_purchase = line3.amount * price     
                    # Calculo el margen estimado
                    if line3.product_id.list_price > 0 and price > 0:
                        estimated_margin = (line3.product_id.list_price / price)-1    
                    else:
                        estimated_margin = 0                  
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line3.product_id.id,
                        'product_sale_id': line3.product_id.id,
                        'name': line3.name,
                        'description': line3.description,
                        'supplier_id': supplierinfo_id.name.id,
                        'purchase_price': price,
                        'sale_price': line3.product_id.list_price,
                        'uom_id': line3.uom_id.id,
                        'amount': line3.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'amortization_rate': 0,
                        'amortization_cost': 0,
                        'indirect_cost_rate': 0,
                        'indirect_cost': 0,
                        'type_cost': line3.type_cost,
                        'type2': line3.type2,
                        'type3': line3.type3,
                        'template_id': src_temp.id,
                        'estimated_date_purchase_completion': estimated_date_purchase_completion,
                        'estimated_margin': estimated_margin
                    }
                    cost_line_obj.create(data)
                else:
                    ### Calculo el total de la venta
                    if product.standard_price:
                        subtotal_purchase = line3.amount * product.standard_price
                    else:
                        subtotal_purchase = 0
                    # Calculo el margen estimado
                    if line3.product_id.list_price > 0 and product.standard_price > 0:
                        estimated_margin = (line3.product_id.list_price / product.standard_price)-1    
                    else:
                        estimated_margin = 0   
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line3.product_id.id,
                        'product_sale_id': line3.product_id.id,
                        'name': line3.name,
                        'description': line3.description,
                        'purchase_price': product.standard_price,
                        'sale_price': line3.product_id.list_price,
                        'uom_id': line3.uom_id.id,
                        'amount': line3.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'amortization_rate': 0,
                        'amortization_cost': 0,
                        'indirect_cost_rate': 0,
                        'indirect_cost': 0,
                        'type_cost': line3.type_cost,
                        'type2': line3.type2,
                        'type3': line3.type3,
                        'template_id': src_temp.id,
                        'estimated_margin': estimated_margin
                    }
                    cost_line_obj.create(data)

            for line4 in src_temp.task_template_lines_ids:
                ### Cojo datos del producto
                product_obj = self.pool.get('product.product')
                product = product_obj.browse(cr, uid, line4.product_id.id)
                ### Cojo el primer proveedor para el producto
                supplierinfo_obj = self.pool.get('product.supplierinfo')
                supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', line4.product_id.id)],                                                                 
                                                                    order='sequence')
                ### Si no tiene cantidad, le pongo 1
                if not line4.amount:
                    line4.amount = 1.0
                ### Diferencio si el producto tiene proveedores o no tiene
                if supplierinfo_ids:
                    supplierinfo_id = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0])
                              
                    partner = self.pool.get('res.partner')
                    supplier = partner.browse(cr, uid, supplierinfo_id.name.id)
                    lang = partner.browse(cr, uid, supplierinfo_id.name.id).lang
                    pricelist_id = supplier.property_product_pricelist_purchase.id
                    #
                    ### Accedo a datos del producto.                                    
                    product_product = self.pool.get('product.product')
                    context_partner = {'lang': lang, 'partner_id': supplierinfo_id.name.id}
                    product = product_product.browse(cr, uid, line4.product_id.id, context=context_partner)                
                    ### Le pongo la fecha del sistema
                    estimated_date_purchase_completion = fields.Date.context_today
                    ### Cojo el precio de compra según tablas.
                    product_pricelist = self.pool.get('product.pricelist')
                    price = product_pricelist.price_get(cr, uid, [pricelist_id], product.id, line4.amount, supplierinfo_id.name.id, {'uom': product.uom_id.id, 'date': estimated_date_purchase_completion})[pricelist_id]                       
                    ### Calculo el total compra
                    subtotal_purchase = line4.amount * price       
                    ### Calculo la amortizacion y los costes indirectos
                    amortization_cost = 0
                    if line4.amortization_rate:
                        if line4.amortization_rate > 0 and subtotal_purchase > 0:
                            amortization_cost = (subtotal_purchase * line4.amortization_rate) / 100
                    indirect_cost = 0
                    if line4.indirect_cost_rate:
                        if line4.indirect_cost_rate > 0 and subtotal_purchase > 0:
                            indirect_cost = (subtotal_purchase * line4.indirect_cost_rate) / 100    
                    # Calculo el margen estimado
                    if line4.product_id.list_price > 0 and price > 0:
                        estimated_margin = (line4.product_id.list_price / price)-1    
                    else:
                        estimated_margin = 0                                      
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line4.product_id.id,
                        'product_sale_id': line4.product_id.id,
                        'name': line4.name,
                        'description': line4.description,
                        'supplier_id': supplierinfo_id.name.id,
                        'purchase_price': price,
                        'sale_price': line4.product_id.list_price,
                        'uom_id': line4.uom_id.id,
                        'amount': line4.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'type_cost': line4.type_cost,
                        'type2': line4.type2,
                        'type3': line4.type3,
                        'amortization_rate': line4.amortization_rate,
                        'amortization_cost': amortization_cost,
                        'indirect_cost_rate': line4.indirect_cost_rate,
                        'indirect_cost': indirect_cost,
                        'template_id': src_temp.id,
                        'estimated_date_purchase_completion': estimated_date_purchase_completion,
                        'estimated_margin': estimated_margin
                    }
                    cost_line_obj.create(data)
                else:
                    ### Calculo el total de la venta
                    if product.standard_price:
                        subtotal_purchase = line4.amount * product.standard_price
                    else:
                        subtotal_purchase = 0          
                    ### Calculo la amortizacion y los costes indirectos
                    amortization_cost = 0
                    if line4.amortization_rate:
                        if line4.amortization_rate > 0 and subtotal_purchase > 0:
                            amortization_cost = (subtotal_purchase * line4.amortization_rate) / 100
                    indirect_cost = 0
                    if line4.indirect_cost_rate:
                        if line4.indirect_cost_rate > 0 and subtotal_purchase > 0:
                            indirect_cost = (subtotal_purchase * line4.indirect_cost_rate) / 100  
                    # Calculo el margen estimado
                    if line4.product_id.list_price > 0 and product.standard_price > 0:
                        estimated_margin = (line4.product_id.list_price / product.standard_price)-1    
                    else:
                        estimated_margin = 0                          
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line4.product_id.id,
                        'product_sale_id': line4.product_id.id,
                        'name': line4.name,
                        'description': line4.description,
                        'purchase_price': product.standard_price,
                        'sale_price': line4.product_id.list_price,
                        'uom_id': line4.uom_id.id,
                        'amount': line4.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'type_cost': line4.type_cost,
                        'type2': line4.type2,
                        'type3': line4.type3,
                        'amortization_rate': line4.amortization_rate,
                        'amortization_cost': amortization_cost,
                        'indirect_cost_rate': line4.indirect_cost_rate,
                        'indirect_cost': indirect_cost,
                        'template_id': src_temp.id,
                        'estimated_margin': estimated_margin
                    }
                    cost_line_obj.create(data)
            for line5 in src_temp.others_template_lines_ids:
                ### Cojo datos del producto
                product_obj = self.pool.get('product.product')
                product = product_obj.browse(cr, uid, line5.product_id.id)
                ### Cojo el primer proveedor para el producto
                supplierinfo_obj = self.pool.get('product.supplierinfo')
                supplierinfo_ids = supplierinfo_obj.search(cr, uid,[('product_id','=', line5.product_id.id)],                                                                 
                                                                    order='sequence')
                ### Si no tiene cantidad, le pongo 1
                if not line5.amount:
                    line5.amount = 1.0
                ### Diferencio si el producto tiene proveedores o no tiene
                if supplierinfo_ids:
                    supplierinfo_id = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0])
                    partner = self.pool.get('res.partner')
                    supplier = partner.browse(cr, uid, supplierinfo_id.name.id)
                    lang = partner.browse(cr, uid, supplierinfo_id.name.id).lang
                    pricelist_id = supplier.property_product_pricelist_purchase.id
                    ### Accedo a datos del producto.
                    product_product = self.pool.get('product.product')
                    context_partner = {'lang': lang, 'partner_id': supplierinfo_id.name.id}
                    product = product_product.browse(cr, uid, line5.product_id.id, context=context_partner)                
                    ### Le pongo la fecha del sistema
                    estimated_date_purchase_completion = fields.Date.context_today
                    ### Cojo el precio de compra según tablas.
                    product_pricelist = self.pool.get('product.pricelist')
                    price = product_pricelist.price_get(cr, uid, [pricelist_id], product.id, line5.amount, supplierinfo_id.name.id, {'uom': product.uom_id.id, 'date': estimated_date_purchase_completion})[pricelist_id]                       
                    ### Calculo el total compra
                    subtotal_purchase = line5.amount * price         
                    ### Calculo la amortizacion y los costes indirectos
                    amortization_cost = 0
                    if line5.amortization_rate:
                        if line5.amortization_rate > 0 and subtotal_purchase > 0:
                            amortization_cost = (subtotal_purchase * line5.amortization_rate) / 100
                    indirect_cost = 0
                    if line5.indirect_cost_rate:
                        if line5.indirect_cost_rate > 0 and subtotal_purchase > 0:
                            indirect_cost = (subtotal_purchase * line5.indirect_cost_rate) / 100  
                    # Calculo el margen estimado
                    if line5.product_id.list_price > 0 and price > 0:
                        estimated_margin = (line5.product_id.list_price / price)-1    
                    else:
                        estimated_margin = 0             
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line5.product_id.id,
                        'product_sale_id': line5.product_id.id,
                        'name': line5.name,
                        'description': line5.description,
                        'supplier_id': supplierinfo_id.name.id,
                        'purchase_price': price,
                        'sale_price': line5.product_id.list_price,
                        'uom_id': line5.uom_id.id,
                        'amount': line5.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'type_cost': line5.type_cost,
                        'type2': line5.type2,
                        'type3': line5.type3,
                        'amortization_rate': line5.amortization_rate,
                        'amortization_cost': amortization_cost,
                        'indirect_cost_rate': line5.indirect_cost_rate,
                        'indirect_cost': indirect_cost,
                        'template_id': src_temp.id,
                        'estimated_date_purchase_completion': estimated_date_purchase_completion
                    }
                    cost_line_obj.create(data)
                else:
                    ### Calculo el total de la venta
                    if product.standard_price:
                        subtotal_purchase = line5.amount * product.standard_price
                    else:
                        subtotal_purchase = 0
                    ### Calculo la amortizacion y los costes indirectos
                    amortization_cost = 0
                    if line5.amortization_rate:
                        if line5.amortization_rate > 0 and subtotal_purchase > 0:
                            amortization_cost = (subtotal_purchase * line5.amortization_rate) / 100
                    indirect_cost = 0
                    if line5.indirect_cost_rate:
                        if line5.indirect_cost_rate > 0 and subtotal_purchase > 0:
                            indirect_cost = (subtotal_purchase * line5.indirect_cost_rate) / 100  
                    # Calculo el margen estimado
                    if line5.product_id.list_price > 0 and product.standard_price > 0:
                        estimated_margin = (line5.product_id.list_price / product.standard_price)-1    
                    else:
                        estimated_margin = 0   
                    data = {
                        'simulation_cost_id': simu_id,
                        'product_id': line5.product_id.id,
                        'product_sale_id': line5.product_id.id,
                        'name': line5.name,
                        'description': line5.description,
                        'purchase_price': product.standard_price,
                        'sale_price': line5.product_id.list_price,
                        'uom_id': line5.uom_id.id,
                        'amount': line5.amount,
                        'subtotal_purchase': subtotal_purchase,
                        'type_cost': line5.type_cost,
                        'type2': line5.type2,
                        'type3': line5.type3,
                        'amortization_rate': line5.amortization_rate,
                        'amortization_cost': amortization_cost,
                        'indirect_cost_rate': line5.indirect_cost_rate,
                        'indirect_cost': indirect_cost,
                        'template_id': src_temp.id,
                        'estimated_margin': estimated_margin
                    }
                    cost_line_obj.create(data)
        return {'type': 'ir.actions.act_window_close'}
