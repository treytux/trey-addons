# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_amount = fields.Float(
        string='Product Amount Total',
        compute='_compute_costs')
    product_cost = fields.Float(
        string='Product Cost',
        compute='_compute_costs')
    timesheet_amount = fields.Float(
        string='Time Amount Total',
        compute='_compute_costs')
    timesheet_cost = fields.Float(
        string='Time Cost',
        compute='_compute_costs')
    total_cost = fields.Float(
        string='Total',
        compute='_compute_costs')

    @api.one
    def _compute_costs(self):
        self.product_amount = sum(
            [l.product_uom_qty for l in self.move_lines2])
        self.product_cost = sum(
            [l.product_id.standard_price * l.product_uom_qty
             for l in self.move_lines2])
        self.timesheet_amount = sum(
            [t.unit_amount for t in self.timesheet_ids])
        self.timesheet_cost = sum(
            [t.product_id.standard_price * t.unit_amount
             for t in self.timesheet_ids])
        self.total_cost = self.timesheet_cost + self.product_cost
