# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models


class product_template(models.Model):
    _inherit = "product.template"

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=100):
        args = args or []
        if name:
            ids = self.search(
                cr, uid,
                ['|', ('name', operator, name),
                 ('default_code', operator, name)] + args,
                limit=limit,
                context=context or {})
        else:
            ids = self.search(cr, uid, args,
                              limit=limit, context=context or {})
        return self.name_get(cr, uid, ids, context or {})
