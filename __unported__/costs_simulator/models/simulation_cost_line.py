# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields
# from tools.translate import _
# import decimal_precision as dp

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class SimulationCostLine(models.Mode):
    _name = 'simulation.cost.line'
    _description = 'Simulation Cost Line'
    
    def _subtotal_purchase_ref(self, cr, uid, ids, name, args, context=None):
        res = {}
        for cost_line in self.browse(cr, uid, ids, context=context):
            if cost_line.purchase_price and cost_line.amount:
                res[cost_line.id] = cost_line.purchase_price * cost_line.amount
            else:
                res[cost_line.id] = 0
                
        return res
    
    def _subtotal_sale_ref(self, cr, uid, ids, name, args, context=None):
        res = {}
        for cost_line in self.browse(cr, uid, ids, context=context):
            if cost_line.sale_price and cost_line.amount:
                res[cost_line.id] = cost_line.sale_price * cost_line.amount
            else:
                res[cost_line.id] = 0
                
        return res
    
    def _benefit_ref(self, cr, uid, ids, name, args, context=None):
        res = {}
        for cost_line in self.browse(cr, uid, ids, context=context):
            if cost_line.subtotal_purchase and cost_line.subtotal_sale:
                res[cost_line.id] = cost_line.subtotal_sale - cost_line.subtotal_purchase - cost_line.amortization_cost - cost_line.indirect_cost
            else:
                res[cost_line.id] = 0
                
        return res
    
    simulation_cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        ondelete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    name = fields.Char(
        string='Name',
        size=64,
        required=True)
    description = fields.Text(
        string='Description')
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier')
    purchase_price =  fields.Float(
        string='Cost Price',
        digits=(7,2))
    uom_id =  fields.Many2one(
        comodel_name='product.uom',
        string='Default Unit Of Measure',
        required=True) 
    amount =  fields.Float(
        string='Amount',
        digits_compute=dp.get_precision('Product UoM'),
        default=1.0)
    subtotal_purchase =  fields.Float(
        string='Subtotal Purchase',
        compute='_subtotal_purchase_ref',
        digits=(7,2),
        store=False)
    product_sale_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    sale_price =  fields.Float(
        string='Sale Price',
        digits=(7,2))
    estimated_margin =  fields.Float(
        string='Estimated Margin',
        digits=(3,4))
    subtotal_sale =  fields.Float(
        string='Subtotal Sale',
        compute='_subtotal_sale_ref',
        digits=(7,2),
        store=False)
    benefit =  fields.Float(
        string='Benefit',
        computed='_benefit_ref',
        digits=(7,2),
        store=False)
    estimated_date_purchase_completion = fields.date(
        string='Estimated Date Purchase Completion',
        default=fields.Date.context_today)
    amortization_rate =  fields.Float(
        string='Amortization Rate',
        digits=(3,2))
    amortization_cost = fields.Float(
        string='Amortization Cost',
        digits=(7,2))   
    indirect_cost_rate = fields.Float(
        string='Indirect Cost Rate',
        igits=(3,2)) 
    indirect_cost = fields.Float(
        string='Indirect Cost',
        digits=(7,2))
    type_cost = fields.selection(
        selection=[
            ('Purchase', 'Purchase'),
            ('Investment', 'Investment'),
            ('Subcontracting Services', 'Subcontracting'),
            ('Task', 'Internal Task'),
            ('Others', 'Others')],
        string='Type of Cost')
    type2 = fields.Selection(
        selection=[
            ('fixed', 'Fixed'),
            ('variable','Variable')],
        string='Fixed/Variable') 
    type3 = fields.Selection(
        selection=[
            ('marketing', 'Marketing'),
            ('sale', 'Sale'),
            ('production', 'Production'),
            ('generalexpenses', 'General Expenses'),
            ('structureexpenses', 'Structure Expenses'),
            ('amortizationexpenses', 'Amortization Expenses')], 
        string='Cost Category') 
    template_id = fields.Many2one(
        comodel_name='simulation.template',
        string='Template')
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale OrdersLines')
    purchase_insale = fields.Boolean(
        string='Copy Purchase information in Sale information',
        related='simulation_cost_id.purchase_insale')

    ### SI CAMBIAN EL PRODUCTO
    @api.one
    def onchange_product(self):
        if self.sale_order_line_id:
            raise exceptions.Warning(
                _('Product Error'),
                _('Yo can not modify the product, this line belongs to a '
                  'line of sale order'))
        res={} 
        if self.product_id:
            if self.type:
                # context_user = {'lang':self.pool.get('res.users').browse(cr, uid, uid).context_lang}
                if self.type == 'Purchase' or self.type == 'Investment' or \
                                self.type == 'Subcontracting Services' or \
                                self.type == 'Task':
                    if not self.product_id.purchase_ok and type != 'Task':
                        raise exceptions.Warning(
                            _('Product Error'),
                            _('Product must be kind to buy'))
                    else:
                        if self.type == 'Purchase' or self.type == \
                                'Investment':
                            if self.product_id.type not in ('product','consu'):
                                raise exceptions.Warning(
                                    _('Product Error'),
                                    _('Product must be product or consumable'))
                        else:
                            if self.type == 'Subcontracting Services' or \
                                            self.type == 'Task':
                                if self.product_id.type != 'service':
                                    raise exceptions.Warning(
                                        _('Product Error'),
                                        _('Product must be a service'))
                                else:
                                    if self.type == 'Subcontracting Services' \
                                            and self.product_id.supply_method \
                                                    != 'buy':
                                        raise exceptions.Warning(
                                            _('Product Error'),
                                            _('Product Supply Method must be '
                                              'BUY'))
                                    else:
                                        if self.type == 'Task' and \
                                                        self.product_id.supply_method != 'produce':
                                             raise exceptions.Warning(
                                                 _('Product Error'),
                                                 _('Product Supply Method must '
                                                   'be PRODUCE'))
                ### COJO EL PRIMER PROVEEDOR PARA EL PRODUCTO
                supplierinfo_obj = self.env['product.supplierinfo']
                supplierinfo_ids = supplierinfo_obj.search([
                    ('product_id','=', self.product.id)],order='sequence')
                if supplierinfo_ids:
                    supplierinfo_id = supplierinfo_obj.browse(supplierinfo_ids[0])
                    supplier = self.env['res.partner'].browse(supplierinfo_id.name.id)
                    lang = self.env['res.partner'].browse(supplierinfo_id.name.id).lang
                    pricelist_id = supplier.property_product_pricelist_purchase.id
                    ### Accedo a datos del producto.                                    
                    product_product = self.env['product.product']
                    context_partner = {
                        'lang': lang,
                        'partner_id': supplierinfo_id.name.id
                    }
                    ### Si no tiene fecha de realización, le pongo la fecha del sistema
                    if not self.estimated_date_purchase_completion:
                        estimated_date_purchase_completion = fields.Date.context_today                  
                    ### Cojo el precio de compra según tablas.  
                    price = 0   
                    for pricelist in supplierinfo_id.pricelist_ids: 
                        if pricelist.min_quantity < self.amount or \
                                        pricelist.min_quantity == self.amount:
                            price = pricelist.price
                    ### Calculo el total compra
                    subtotal_purchase = self.amount * price
                    amortization_cost = 0.0
                    indirect_cost = 0.0
                    ### Miro si tengo que calcular la amortizacion y los costes indirectos
                    if self.type == 'Task' or self.type == 'Others': 
                        ### Calculo la amortizacion
                        amortization_cost = 0.0
                        if self.product_id.amortization_rate:
                            if self.product_id.amortization_rate > 0 and \
                                            subtotal_purchase > 0:
                                amortization_cost = (subtotal_purchase * 
                                                     self.product_id.amortization_rate) / 100
                        ### Calculo los costes indirectos
                        indirect_cost = 0.0
                        if self.product_id.indirect_cost_rate:
                            if self.product_id.indirect_cost_rate > 0 and \
                                            subtotal_purchase > 0:
                                indirect_cost = (subtotal_purchase * 
                                                 self.product_id.indirect_cost_rate) / 100         
                    benefit = self.sale_subtotal - subtotal_purchase - \
                              amortization_cost - indirect_cost           
                    #              
                    if self.type == 'Task':
                        # Si es una linea que viene de la pestaña TASK
                        # cargo datos sin proveedor
                        res = {
                            'name': self.product_id.name or '',
                            'description': self.product_id_id.description or '',
                            'purchase_price': price,
                            'uom_id': self.product_id.uom_id.id,
                            'amount': self.amount,
                            'supplier_id': None,
                            'subtotal_purchase': subtotal_purchase,
                            'amortization_rate': self.product_id.amortization_rate,
                            'amortization_cost': amortization_cost,
                            'indirect_cost_rate': self.product_id.indirect_cost_rate,
                            'indirect_cost':indirect_cost,
                            'benefit':benefit,
                            'sale_product_id': self.product_id_id,
                            'sale_price': self.product_id.list_price
                        }
                    else:
                        # Si es una linea que viene de la pestaña TASK (Internal task)
                        # cargo datos con proveedor
                        if self.type == 'Others':
                            res = {
                                'name': self.product.name or '',
                                'description': self.product.description or '',
                                'purchase_price': price,
                                'uom_id': self.product.uom_id.id,
                                'amount': self.amount,
                                'supplier_id': supplierinfo_id.name.id,
                                'subtotal_purchase': subtotal_purchase,
                                'amortization_rate': self.product.amortization_rate,
                                'amortization_cost': amortization_cost,
                                'indirect_cost_rate': 
                                    self.product.indirect_cost_rate,
                                'indirect_cost':indirect_cost,
                                'benefit':benefit,
                                'sale_product_id': self.product_id,
                                'sale_price': self.product.list_price
                            }
                        else:
                            res = {
                                'name': self.product_id.name or '',
                                'description': self.product_id.description
                                               or '',
                                'purchase_price': price,
                                'uom_id':self.product_id.uom_id.id,
                                'amount':self.amount,
                                'supplier_id': supplierinfo_id.name.id,
                                'subtotal_purchase': subtotal_purchase,
                                'amortization_rate': 0,
                                'amortization_cost': 0,
                                'indirect_cost_rate': 0,
                                'indirect_cost': 0,
                                'benefit':benefit,
                                'sale_product_id': self.product_id,
                                'sale_price': self.product_id.list_price
                            }
                            
                else:
                    if self.product_id.standard_price:
                        subtotal_purchase = self.amount * \
                                            self.product_id.standard_price
                    else:
                        subtotal_purchase = 0
                    amortization_cost = 0.0
                    indirect_cost = 0.0
                    if self.type == 'Task' or self.type == 'Others':
                        ### Calculo la amortizacion
                        amortization_cost = 0.0
                        if self.product_id.amortization_rate:
                            if self.product_id.amortization_rate > 0 and \
                                            subtotal_purchase > 0:
                                amortization_cost = (subtotal_purchase *
                                                     self.product_id.amortization_rate) / 100
                        ### Calculo los costes indirectos
                        indirect_cost = 0.0
                        if self.product_id.indirect_cost_rate:
                            if self.product_id.indirect_cost_rate > 0 and \
                                            subtotal_purchase > 0:
                                indirect_cost = (subtotal_purchase *
                                                 self.product_id.indirect_cost_rate) / 100
                        
                        benefit = self.sale_subtotal - subtotal_purchase - \
                                  amortization_cost - indirect_cost
                        res = {
                            'name': self.product_id.name or '',
                            'description': self.product_id.description or '',
                            'purchase_price': self.product_id.standard_price or '',
                            'uom_id':self.product_id.uom_id.id,
                            'amount':self.amount,
                            'supplier_id': None,
                            'subtotal_purchase': subtotal_purchase,
                            'amortization_rate': self.product_id.amortization_rate,
                            'amortization_cost': amortization_cost,
                            'indirect_cost_rate': self.product_id.indirect_cost_rate,
                            'indirect_cost':indirect_cost,
                            'benefit':benefit,
                            'sale_product_id': self.product_id.id,
                            'sale_price': self.product_id.list_price
                        }
                    else:   
                        benefit = self.sale_subtotal - subtotal_purchase - \
                                  amortization_cost - indirect_cost
                        res = {
                            'name': self.product_id.name or '',
                            'description': self.product_id.description or '',
                            'purchase_price': self.product_id.standard_price or '',
                            'uom_id':self.product_id.uom_id.id,
                            'amount':self.amount,
                            'supplier_id': None,
                            'subtotal_purchase': subtotal_purchase,
                            'amortization_rate': 0,
                            'amortization_cost': 0,
                            'indirect_cost_rate': 0,
                            'indirect_cost': 0,
                            'benefit':benefit,
                            'sale_product_id': self.product_id.id,
                            'sale_price': self.product_id.list_price
                        }
        ### DEVUELVO VALORES
        return {'value': res}
    ### SI CAMBIAN EL PROVEEDOR
    @api.one
    def onchange_supplier(self, supplier_id, type_cost, product_id, amount,
                          uom_id, estimated_date_purchase_completion,
                          subtotal_purchase, sale_price, subtotal_sale,
                          estimated_margin, benefit, sale_order_line_id):
        if sale_order_line_id:
            raise exceptions.Warning(
                _('Supplier Error'),
                _('Yo can not modify the supplier, this line belongs to a '
                  'line of sale order'))
        res={}      
        if self.supplier_id:
            if not product_id:
                raise exceptions.Warning(
                    _('Supplier Error'),
                    _('You must select a product'))
            else:   
                #
                ### Accedo a datos del proveedor
                # partner = self.pool.get('res.partner')
                # supplier = partner.browse(cr, uid, supplier_id)
                # lang = partner.browse(cr, uid, supplier_id).lang
                supplier_id.property_product_pricelist_purchase.id
                #
                ### Accedo a datos del producto.                                    
                # product_product = self.pool.get('product.product')
                # context_partner = {'lang': lang, 'partner_id': supplier_id}
                # product = product_product.browse(cr, uid, product_id, context=context_partner)
                #
                ### Si no tiene fecha de realización, le pongo la fecha del sistema
                if not estimated_date_purchase_completion:
                    estimated_date_purchase_completion = \
                        fields.Date.context_today
                #
                ### Si no tiene cantidad, le pongo 1
                if not amount:
                    amount = 1.0       
                ### Cojo el precio de compra según tablas.
                # product_pricelist = self.pool.get('product.pricelist')
                price = self.env['product.pricelist'].price_get(
                    [self.product_id.pricelist_id], self.product_id.id, amount,
                    supplier_id,
                    {'uom': uom_id,
                     'date': estimated_date_purchase_completion})#[
                     # pricelist_id]
                ### Calculo el total compra
                subtotal_purchase = amount * price
                ### Calculo el total venta
                if sale_price > 0:
                    subtotal_sale = amount * sale_price
                else:
                    subtotal_sale = 0;
                ### Calculo el margen estimado
                if price > 0 and sale_price > 0:
                    estimated_margin =(sale_price/price)-1
                else:
                    estimated_margin = 0                    
                ### Calculo el beneficio
                benefit = subtotal_sale - subtotal_purchase
                #
                ### Miro si tengo que calcular la amortizacion y los costes indirectos
                if self.type_cost == 'Task' or self.type_cost == 'Others':
                    ### Calculo la amortizacion
                    amortization_cost = 0.0
                    if self.product_id.amortization_rate:
                        if self.product_id.amortization_rate > 0 and \
                                        subtotal_purchase > 0:
                            amortization_cost = (subtotal_purchase *
                                                 self.product_id.amortization_rate) / 100
                    ### Calculo los costes indirectos
                    indirect_cost = 0.0
                    if self.product_id.indirect_cost_rate:
                        if self.product_id.indirect_cost_rate > 0 and \
                                        subtotal_purchase > 0:
                            indirect_cost = (subtotal_purchase *
                                             self.product_id.indirect_cost_rate) / 100
                    ### Cargo campos de pantalla
                    benefit = subtotal_sale - subtotal_purchase - amortization_cost - indirect_cost
                    res.update({
                        'purchase_price': price,
                        'amount': amount,
                        'estimated_date_purchase_completion':  estimated_date_purchase_completion,
                        'subtotal_purchase': subtotal_purchase,
                        'subtotal_sale': subtotal_sale,
                        'estimated_margin': estimated_margin,
                        'benefit': benefit,
                        'estimated_date_purchase_completion': estimated_date_purchase_completion,
                        'amortization_rate':
                            self.product_id.amortization_rate,
                        'amortization_cost': amortization_cost,
                        'indirect_cost_rate':
                            self.product_id.indirect_cost_rate,
                        'indirect_cost':indirect_cost
                    })
                else:
                    #
                    ### Cargo campos de pantalla
                    res.update({
                        'purchase_price': price,
                        'amount': amount,
                        'estimated_date_purchase_completion':  estimated_date_purchase_completion,
                        'subtotal_purchase': subtotal_purchase,
                        'subtotal_sale': subtotal_sale,
                        'estimated_margin': estimated_margin,
                        'benefit': benefit,
                        'estimated_date_purchase_completion': estimated_date_purchase_completion,
                        'amortization_rate': 0,
                        'amortization_cost': 0,
                        'indirect_cost_rate': 0,
                        'indirect_cost': 0
                    })
        ### DEVUELVO VALORES
        return {'value': res}
    
    ### SI CAMBIAN EL PRECIO O CANTIDAD DEL PRODUCTO A COMPRAR, CALCULO EL TOTAL
    @api.one
    def onchange_purchase_price_amount(self, type_cost, amortization_rate,
                                       indirect_cost_rate, purchase_price,
                                       amount, subtotal_purchase,
                                       sale_price, subtotal_sale,
                                       estimated_margin, benefit,
                                       sale_order_line_id, purchase_insale):
        if sale_order_line_id:
            raise exceptions.Warning(
                _('Price/Amount Error'),
                _('Yo can not modify the price/ammount, this line belongs to a'
                  ' line of sale order'))
        res={}
        if purchase_price and amount:
            ### Calculo el total de la compra
            if purchase_price > 0 and amount > 0:
                subtotal_purchase = amount * purchase_price
            else:
                subtotal_purchase = 0
            ### Si esta activado copiar informacion de compra en venta
            if purchase_insale == True:
                sale_price = purchase_price
            ### Calculo el total de la venta
            if sale_price > 0 and amount > 0:
                subtotal_sale = amount * sale_price
            else:
                subtotal_sale = 0
            ### Calculo el margen estimado
            if purchase_price > 0 and sale_price > 0:
                estimated_margin =(sale_price/purchase_price)-1
            else:
                estimated_margin = 0
            ### Calculo el beneficio
            benefit = subtotal_sale - subtotal_purchase
            ### Calculo la amortizacion y los costes indirectos
            if (self.type_cost == 'Task') or (self.type_cost == 'Others'):
                ### Calculo la amortizacion
                amortization_cost = 0.0
                if amortization_rate:
                    if amortization_rate > 0 and subtotal_purchase > 0:
                        amortization_cost = (subtotal_purchase * amortization_rate) / 100
                ### Calculo los costes indirectos
                indirect_cost = 0.0
                if indirect_cost_rate:
                    if indirect_cost_rate > 0 and subtotal_purchase > 0:
                        indirect_cost = (subtotal_purchase * indirect_cost_rate) / 100  
                ### Cargo campos de pantalla
                benefit = subtotal_sale - subtotal_purchase - amortization_cost - indirect_cost  
                res.update({
                    'subtotal_purchase': subtotal_purchase,
                    'estimated_margin': estimated_margin,
                    'subtotal_sale': subtotal_sale,
                    'benefit': benefit,
                    'amortization_cost': amortization_cost,
                    'indirect_cost': indirect_cost,
                    'sale_price': sale_price
                })
            else:
                ### Cargo campos de pantalla
                res.update({
                    'subtotal_purchase': subtotal_purchase,
                    'estimated_margin': estimated_margin,
                    'subtotal_sale': subtotal_sale,
                    'benefit': benefit,
                    'amortization_rate': 0,
                    'amortization_cost': 0,
                    'indirect_cost_rate': 0,
                    'indirect_cost': 0,
                    'sale_price': sale_price})
        ### DEVUELVO VALORES
        return {'value': res}
    ### SI CAMBIA EL TIPO DE COSTE
    @api.one
    def onchange_type_cost(self):
        res={
            'product_id':'',
            'name':'',
            'description':'',
            'uom_id':'',
            'supplier_id':'',
            'purchase_price':0,
            'amount':0,
            'subtotal_purchase':0,
            'product_sale_id':'',
            'sale_price':0,
            'estimated_margin':0,
            'subtotal_sale':0,
            'benefit':0,
            'amortization_rate': 0,
            'amortization_cost': 0,
            'indirect_cost_rate': 0,
            'indirect_cost': 0}
        return {'value': res}     
    ### SI CAMBIAN EL PRODUCTO DE VENTA
    @api.one
    def onchange_sale_product(self, product_sale_id, product_id,
                              purchase_price, amount, subtotal_sale,
                              estimated_margin, subtotal_purchase, benefit,
                              sale_order_line_id, amortization_cost,
                              indirect_cost):
        if sale_order_line_id:
            raise exceptions.Warning(
                _('Sale Product Error'),
                _('Yo can not modify the sale product, this line belongs to a '
                  'line of sale order'))
        res={} 
        if self.product_sale_id and self.product_id:
            ### Cojo datos del producto de venta
            # product_obj = self.pool.get('product.product')
            # product = product_obj.browse(cr, uid, product_sale_id)
            if self.product_sale_id != self.product_id:
                if not self.product_sale_id.sale_ok:
                    raise exceptions.Warning(
                        _('Sale Product Error'),
                        _('Product must be to sale OR the same product of '
                          'purchase'))
            #
            ### Calculo el total de la venta
            if self.product_sale_id.list_price > 0 and amount > 0:
                subtotal_sale = amount * self.product_sale_id.list_price
            else:
                subtotal_sale = 0
            ### Calculo el margen estimado
            if purchase_price > 0 and self.product_sale_id.standard_price > 0:
                estimated_margin = (self.product_sale_id.list_price/purchase_price)-1
            else:
                estimated_margin=0
            ### Calculo el beneficio
            benefit = subtotal_sale - subtotal_purchase - amortization_cost - indirect_cost
            #
            ### Cargo campos de pantalla           
            res.update({
                'sale_price': self.product_sale_id.list_price or '',
                'estimated_margin': estimated_margin,
                'subtotal_sale': subtotal_sale,
                'benefit': benefit
            })
        ### DEVUELVO VALORES
        return {'value': res}
    
    #
    ### SI CAMBIAN EL PRECIO DE VENTA
    #
    @api.one
    def onchange_sale_price(self, purchase_price, amount, sale_price,
                            subtotal_sale, estimated_margin, subtotal_purchase,
                            benefit, sale_order_line_id, amortization_cost,
                            indirect_cost):
        if sale_order_line_id:
            raise exceptions.Warning(
                _('Sale Price Error'),
                _('Yo can not modify the sale price, this line belongs to a '
                  'line of sale order'))
        res={}
        if sale_price:
            ### Calculo el total de la venta
            if sale_price > 0 and amount > 0:
                subtotal_sale = amount * sale_price
            else:
                subtotal_sale = 0    
            ### Calculo el margen estimado
            if purchase_price > 0 and sale_price > 0:
                estimated_margin =(sale_price/purchase_price)-1
            else:
                estimated_margin = 0
            ### Calculo el beneficio
            benefit = subtotal_sale - subtotal_purchase - amortization_cost - indirect_cost
            ### Cargo campos de pantalla
            res.update({
                'estimated_margin': estimated_margin,
                'subtotal_sale': subtotal_sale,
                'benefit': benefit})
        ### DEVUELVO VALORES
        return {'value': res}
    ### SI CAMBIAN EL MARGEN ESTIMADO
    @api.one
    def onchange_estimated_margin(self, estimated_margin, purchase_price,
                                  sale_price, amount, subtotal_sale,
                                  subtotal_purchase, benefit,
                                  sale_order_line_id, amortization_cost,
                                  indirect_cost):
        if sale_order_line_id:
            raise exceptions.Warning(
                _('Estimated Margin Error'),
                _('You can not modify the estimated margin, this line '
                  'belongs to a line of sale order'))
        res={}
        if estimated_margin:
            ### Calculo el precio de venta
            if purchase_price > 0 and estimated_margin > 0:
                sale_price = (1+estimated_margin) * purchase_price
            else:
                sale_price = 0
            ### Calculo el total de la venta
            if sale_price > 0 and amount > 0:
                subtotal_sale = amount * sale_price
            else:
                subtotal_sale = 0
            ### Calculo el beneficio
            benefit = subtotal_sale - subtotal_purchase -amortization_cost - indirect_cost
            ### Cargo campos de pantalla
            res.update({
                'sale_price': sale_price,
                'subtotal_sale': subtotal_sale,
                'benefit': benefit
            })
        ### DEVUELVO VALORES
        return {'value': res}
