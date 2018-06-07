# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_quotation_send(self):
        def_template = self.company_id.default_sale_order_email_template
        res = super(SaleOrder, self).action_quotation_send()
        if not def_template:
            return res
        res['context']['default_template_id'] = def_template.id
        res['context']['default_use_template'] = True
        return res
