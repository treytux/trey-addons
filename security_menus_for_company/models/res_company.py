# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    hidden_menu_ids = fields.Many2many(
        comodel_name="ir.ui.menu",
        relation="ir_ui_menu_in_res_company_rel",
        column1="company_id",
        column2="menu_id",
        string="Hidden Menus"
    )

    @api.one
    def write(self, vals):
        '''Limpia la cache en el caso de ocultar un menu.'''

        if 'hidden_menu_ids' in vals:
            self.env['ir.ui.menu'].clear_caches()
        return super(ResCompany, self).write(vals)
