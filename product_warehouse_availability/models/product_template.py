# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_template_availability(self):
        ctx = self.env.context.copy()
        self.env[
            'product.product.warehouse.availability'].product_availability(
                template=self, product=None, company=self.env.user.company_id)
        ctx.update({
            'search_default_product_tmpl_id': self.id,
            'group_default_product_tmpl_id': self.id,
        })
        return {
            'name': _('Product warehouse availability'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'product.product.warehouse.availability',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
