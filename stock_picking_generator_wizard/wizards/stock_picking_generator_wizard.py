from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import fields, models


class StockPickingGeneratorWizard(models.Model):
    _name = 'stock.picking.generator.wizard'

    quantity = fields.Integer(
        string='Quantity',
        default=1,
    )
    period = fields.Integer(
        string='Period',
        default=0,
    )
    period_unit = fields.Selection(
        [('days', 'Days'), ('months', 'Months'), ('years', 'Years')],
        string='Period Unit',
        default='days',
    )
    product = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        required=True,
    )
    partner_id = fields.Many2one(
        string='Customer',
        comodel_name='res.partner',
        required=True,
    )

    def action_create_pickings(self):
        self.ensure_one()
        Picking = self.env['stock.picking']
        pickings_created = []
        base_dt = datetime.utcnow()
        for i in range(self.quantity):
            if self.period_unit == 'days':
                dt = base_dt + relativedelta(days=self.period * i)
            elif self.period_unit == 'months':
                dt = base_dt + relativedelta(months=self.period * i)
            else:
                dt = base_dt + relativedelta(years=self.period * i)
            picking_type_id = self.env.ref(
                'stock_picking_generator_wizard.stock_picking_type_ts_test')
            src_loc = (picking_type_id.default_location_src_id
                       and picking_type_id.default_location_src_id.id or False)
            dest_loc = (picking_type_id.default_location_dest_id
                        and picking_type_id.default_location_dest_id.id
                        or False)
            move_vals = {
                'name': (self.product.name_get()[0][1] if self.product
                         else 'visit product'),
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product.uom_id.id,
                'location_id': src_loc,
                'location_dest_id': dest_loc,
            }
            picking = Picking.create({
                'partner_id': self.partner_id.id,
                'picking_type_id': picking_type_id.id,
                'scheduled_date': fields.Datetime.to_string(dt),
                'move_ids': [(0, 0, move_vals)],
            })
            pickings_created.append(picking.id)
        action = {
            'name': 'visit pickings',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', pickings_created)],
            'context': {'search_default_groupby_picking_type': 1},
        }
        return action
