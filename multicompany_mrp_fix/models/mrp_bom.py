# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def _bom_find(
            self, cr, uid, product_tmpl_id=None, product_id=None,
            properties=None, context=None):
        if context is None:
            context = {}
        company = [p for p in properties or [] if 'company:' in p]
        if company:
            properties.remove(company[0])
            context['company_id'] = company[0].split(':')[1]
        if 'current_company_id' in context:
            context['company_id'] = context['current_company_id']
        return super(MrpBom, self)._bom_find(
            cr, uid, product_tmpl_id, product_id, properties, context)
