# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _
from datetime import timedelta


class ProductSold(models.Model):
    _name = 'product.sold'
    _description = 'Product Sold'
    _display_name = 'lot_id'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')
    seller_id = fields.Many2one(
        comodel_name='res.partner',
        string='Seller')
    installer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Installer')
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        required=True,
        string='Serial')
    product_id = fields.Many2one(
        related='lot_id.product_id',
        string='Product',
        store=True)
    date_register = fields.Date(
        string='Register',
        required=True,
        default=fields.Date.today)
    date_buy = fields.Date(
        string='Buy')
    date_startup = fields.Date(
        string='StartUp')
    date_startup_register = fields.Date(
        string='StartUp Register')
    buy_ticket = fields.Binary(string='Ticket')
    warranty = fields.Binary(string='Warranty Certificate')
    startup = fields.Binary(string='StartUp Certificate')
    claim_count = fields.Integer(
        string='Claim count',
        compute='_compute_claim_count')
    register_startup_in_time = fields.Boolean(
        compute='_compute_dates',
        string='Register Startup in Time')

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            name = obj.lot_id and obj.lot_id.name or 'Unknow'
            res.append((obj.id, name))
        return res

    @api.one
    def _compute_claim_count(self):
        self.claim_count = self.env['crm.claim'].search_count(
            [('sold_id', '=', self.id)])

    @api.one
    @api.depends('date_register', 'date_buy',
                 'date_startup', 'date_startup_register')
    def _compute_dates(self):
        if self.date_startup and self.date_startup_register:
            startup = fields.Date.from_string(self.date_startup)
            startup_limit = startup + timedelta(days=30)
            register = fields.Date.from_string(self.date_startup_register)
            self.register_startup_in_time = bool(register <= startup_limit)
        else:
            self.register_startup_in_time = False

    @api.multi
    def claim_tree_view(self):
        return {
            'name': _('Crm Claim'),
            'domain': [('sold_id', '=', self.id)],
            'res_model': 'crm.claim',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s', "
                       "'default_res_id': %d, "
                       "'search_default_sold_id': %d, "
                       "'default_sold_id': %d}" % (
                self._name,
                self.id,
                self.id,
                self.id)}
