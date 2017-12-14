# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, fields, exceptions, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    default_code = fields.Char(
        copy=False)

    @api.one
    @api.constrains('default_code')
    def _check_default_code(self):
        if self.default_code:
            default_code = self.search([
                ('id', '!=', self.id),
                ('default_code', '=', self.default_code)], limit=1)

            if default_code:
                raise exceptions.Warning(
                    _("Error! The Default Code %s already exists" %
                      self.default_code)
                )
