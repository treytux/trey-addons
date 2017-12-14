# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('project_id')
    def onchange_project_id(self):
        if not self.project_id:
            return
        project = self.env['project.project'].search(
            [('analytic_account_id', '=', self.project_id.id)])
        if not project or not project[0].sale_order_type_id:
            self.type_id = None
            return
        self.type_id = project[0].sale_order_type_id.id
