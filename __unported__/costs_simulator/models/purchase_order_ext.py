# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields
# from tools.translate import _

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

### IMPORTO ESTA CLASE PARA AÑADIR CAMPOS


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    
    def _catch_default_type(self, cr, uid, context=None):
        if not context:
            context = {}
            
        purchase_type_obj = self.pool.get('purchase.type')
        purchase_type_ids = purchase_type_obj.search(cr,uid,[('name','=','Others')])
        if not purchase_type_ids:
            raise osv.except_osv(_('Purchase Type ERROR'),_('OTHERS purchase type NOT FOUND'))
        else:
            for purchase_type_id in purchase_type_ids:
                return purchase_type_id

    # Campo para saber que pedidos de compra se han generado
    # a partir del pedido de venta
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order')
    # Campo para relacionar los pedidos de compra con el subsubproyecto
    project2_id = fields.Many2one(
        comodel_name='project.project',
        string='Subsubproject')
    # Campo para relacionar los pedidos de compra con el Projecto
    project3_id = fields.Many2one(
        comodel_name='project.project',
        string='Project')
    # Campo para saber a que tipo de coste pertenece la orden de pedido de compra
    type_cost = fields.Char(
        string='Type Cost',
        size=64)
    # Tipo de compra
    type = fields.Many2one(
        comodel_name='purchase.type',
        string='Type',
        default='_catch_default_type',
        required=True)
    #
    ### SI CAMBIAN EL TIPO DE COMPRA
    #
    def onchange_purchase_type(self, cr, uid, ids, type, context=None):
        res={}
        if type:
            purchase_type_obj = self.pool.get('purchase.type')
            purchase_type = purchase_type_obj.browse(cr, uid, type)
            code = purchase_type.sequence.code
            seq = self.pool.get('ir.sequence').get(cr,uid,code)
            res.update({'name':seq})
                     
        return {'value': res} 
    
    @api.one
    def wkf_confirm_order(self):
        res = super(PurchaseOrder, self).wkf_confirm_order()
        return res
