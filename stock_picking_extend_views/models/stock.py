# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.


from openerp import models, fields


class stock_picking(models.Model):
    _inherit = "stock.picking"

    salesman_id = fields.Many2one(
        comodel_name='res.users',
        string='Comercial',
        related='partner_id.user_id',
        store=True,
        readonly=True
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Provincia',
        related='partner_id.state_id',
        store=True, readonly=True
    )
