# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.multi
    @api.returns('self')
    def _filter_visible_menus(self):
        res = super(IrUiMenu, self)._filter_visible_menus()
        if self.env.user.company_id.hidden_menu_ids:
            return res.filtered(lambda menu:
                                menu not in
                                self.env.user.company_id.hidden_menu_ids
                                )
        return res
