# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields
# from tools.translate import _
# import decimal_precision as dp

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class SimulationTemplateLine(models.Model):

    _name = 'simulation.template.line'
    _description = 'Simulation Template Line'

    template_id = fields.Many2one(
        comodel_name='simulation.template',
        string='Template',
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
    amortization_rate = fields.Float(
        string='Amortization Rate',
        digits=(3,2))
    indirect_cost_rate = fields.Float(
        string='Indirect Cost Rate',
        digits=(3,2))
    amount = fields.Float(
        string='Amount',
        digits_compute=dp.get_precision('ProductUoM'),
        default=1.0),
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Default Unit Of Measure',
        required=True)
    type_cost = fields.selection(
        selection=[
            ('Purchase','Purchase'),
           ('Investment','Investment'),
           ('Subcontracting Services','Subcontracting'),
           ('Task','Internal Task'),
           ('Others','Others')],
        string='Type of Cost')
    type2 = fields.selection(
        selection=[
            ('fixed','Fixed'),
            ('variable','Variable')],
        string='Fixed/Variable')
    type3 = fields.selection(
        selection=[
            ('marketing','Marketing'),
            ('sale','Sale'),
            ('production','Production'),
            ('generalexpenses','General Expenses'),
            ('structureexpenses','Structure Expenses'),
            ('amortizationexpenses', 'Amortization Expenses')],
        string='Cost Category')

    ### SI CAMBIAN EL PRODUCTO, COJO SU NOMBRE Y LO MUESTRO
    ### EN EL FORM DE LA LINEA DE SIMULACION
    @api.one
    def onchange_product(self, product_id, type):
        if self.product_id:
            if type:
                product_obj = self.pool.get('product.product')
                product = product_obj.browse(cr, uid, product_id)
                if self.type == 'Purchase' or self.type == 'Investment' or \
                                self.type == 'Subcontracting Services' or \
                                self.type == 'Task':
                    if not product.purchase_ok and type != 'Task':
                        raise exceptions.Warning(
                            _('Product Error'),
                            _('Product must be kind to buy'))
                    else:
                        if self.type == 'Purchase' or self.type == \
                                'Investment':
                            if product.type != 'product' and product.type != 'consu':
                                raise exceptions.Warning(
                                    _('Product Error'),
                                    _('Product must be product or consumable'))
                        else:
                            if self.type == 'Subcontracting Services' or \
                                            self.type == 'Task':
                                if product.type != 'service':
                                    raise exceptions.Warning(
                                        _('Product Error'),
                                        _('Product must be a service'))
                                else:
                                    if self.type == 'Subcontracting Services' \
                                            and product.supply_method != 'buy':
                                        raise exceptions.Warning(
                                            _('Product Error'),
                                            _('Product Supply Method must be '
                                              'BUY'))
                                    else:
                                        if self.type == 'Task' and \
                                                        product.supply_method != 'produce':
                                             raise exceptions.Warning(
                                                 _('Product Error'),
                                                 _('Product Supply Method must'
                                                   ' be PRODUCE'))
                ### PARA PODER UTILIZAR _('\n), AL PRINCIPIO DEBEMOS DE IMPORTAR
                ### from tools.translate import _
                if self.type == 'Task' or self.type == 'Others':
                    res = {
                        'name': product.name or '',
                        'description': product.description or '',
                        'uom_id':product.uom_id.id,
                        'amortization_rate': product.amortization_rate,
                        'indirect_cost_rate': product.indirect_cost_rate
                    }
                else:
                    res = {
                        'name': (product.name or ''),
                        'description': (product.description or ''),
                        'uom_id':product.uom_id.id}
                return {'value': res}
    ### SI CAMBIA EL TIPO DE COSTE
    @api.one
    def onchange_type_cost(self, type):
        res={
            'product_id':'',
            'name':'',
            'description':'',
            'uom_id':'',
            'amount':0
        }
        return {'value': res}
