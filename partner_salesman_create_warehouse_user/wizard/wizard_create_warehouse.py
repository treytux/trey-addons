# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _


class WizCreateWarehouse(models.TransientModel):
    _name = 'wiz.create_warehouse'

    name = fields.Char(
        string='Empty')
    warehouse_name = fields.Char(
        string='Warehouse name',
        required=True)
    warehouse_code = fields.Char(
        string='Warehouse code',
        size=5,
        required=True)

    @api.one
    def button_accept(self):
        '''Create a warehouse and assign it to user.'''
        context = self.env.context
        if len(context.get('active_ids')) > 1:
            raise exceptions.Warning(_('You must select only one user!'))
        user = self.env['res.users'].browse(context.get('active_id'))
        if user.partner_is_salesman:
            data = {
                'name': self.warehouse_name,
                'code': self.warehouse_code}
            warehouse = self.env['stock.warehouse'].create(data)
            user.write({'warehouse_id': warehouse.id})
        return True
