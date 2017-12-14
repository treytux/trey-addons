# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api


class product_template(models.Model):
    _inherit = "product.template"

    @api.depends(lambda self: (self._rec_name,) if self._rec_name else ())
    def _compute_display_name(self):
        for i, got_name in enumerate(self.name_get()):
            if self[i].default_code:
                self[i].display_name = u'[{}] {}'.format(self[i].default_code,
                                                         got_name[1])
            else:
                self[i].display_name = got_name[1]
