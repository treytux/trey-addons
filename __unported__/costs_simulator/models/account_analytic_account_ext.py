# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
##

# from osv import osv
# from osv import fields
# import decimal_precision as dp

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


#
### HEREDO ESTA CLASE PARA AÑADIR LOS CAMPOS DE IMPORTE DE VENTA ESTIMADA,
### E IMPORTE DE COSTE ESTIMADO A LA CLASE account.analytic.account
#
class AccountAnalyticAccount(models.Model):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'

    @api.multi
    def name_get(self):
        res = []
        for account in self:
            data = []
            acc = account
            if acc: 
                data.insert(0, acc.name)
            data = ' / '.join(data)
            res.append((account.id, data))
        return res

    estimated_balance = fields.Float(
        string='Estimated Balance',
        readonly=True,
        digits_compute=dp.get_precision('Account'))
    estimated_cost = fields.Float(
        string='Estimated Cost',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    estimated_sale = fields.Float(
        string='Estimated Sale',
        readonly=True,
        digits_compute=dp.get_precision('Sale Price'))

    
    # def ButtonAnalyticalStructureUpdateCosts(self):
    #
    #    return True
    #
