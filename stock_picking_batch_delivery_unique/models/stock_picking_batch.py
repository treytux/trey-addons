###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )
    number_of_packages = fields.Integer(
        string='Number of packages',
        compute='_compute_number_of_packages',
    )
    total_weight = fields.Float(
        string='Total weight',
        compute='_compute_total_weight',
    )
    total_volume = fields.Float(
        string='Total volume',
        compute='_compute_total_volume',
    )
    shipping_weight = fields.Float(
        string='Shipping weight',
    )
    shipping_volume = fields.Float(
        string='Shipping volume',
    )

    def create_simulate_stock_picking(self):
        partners = list(set(self.picking_ids.mapped('partner_id')))
        if len(partners) != 1:
            raise exceptions.ValidationError(
                _('Delivery: Different partners in the same group'))
        carriers = list(set(self.picking_ids.mapped('carrier_id')))
        if len(carriers) != 1:
            raise exceptions.ValidationError(
                _('Delivery: Different carriers in the same in group'))
        move_lines = []
        for move in self.picking_ids.mapped('move_lines').filtered(
                lambda l: l.state == 'assigned'):
            move_lines.append({
                'name': move.name,
                'product_id': move.product_id.id,
                'product_uom': move.product_uom.id,
                'product_uom_qty': move.product_uom_qty,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
            })
        return self.env['stock.picking'].create({
            'name': self.name,
            'partner_id': partners[0].id,
            'carrier_id': carriers[0].id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_output').id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_lines': [(0, 0, m) for m in move_lines],
        })

    def get_picking_attachments(self, picking):
        return self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])

    def add_shipping_info(self, picking, info):
        picking.write({
            'carrier_tracking_ref': info[0]['tracking_number'],
            'carrier_price': info[0]['exact_price'],
        })
        return True

    @api.multi
    def done(self):
        res = super().done()
        simulate_picking = self.create_simulate_stock_picking()
        info = simulate_picking.carrier_id.send_shipping(simulate_picking)
        attachment_obj = self.env['ir.attachment']
        attachments = self.get_picking_attachments(simulate_picking)
        for picking in self.picking_ids.filtered(lambda p: p.state == 'done'):
            self.add_shipping_info(picking, info)
            for attachment in attachments:
                attachment_obj.create({
                    'name': attachment.name,
                    'datas': attachment.datas,
                    'datas_fname': attachment.datas_fname,
                    'res_model': 'stock.picking',
                    'res_id': picking.id,
                    'mimetype': attachment.mimetype,
                })
        simulate_picking.unlink()
        return res

    @api.depends('picking_ids')
    def _compute_number_of_packages(self):
        for batch in self:
            batch.number_of_packages = sum(
                [picking.number_of_packages for picking in batch.picking_ids
                    if picking.state != 'cancel'])

    @api.depends('picking_ids')
    def _compute_total_weight(self):
        for batch in self:
            for picking in batch.picking_ids:
                picking._cal_weight()
            batch.total_weight = sum(
                [picking.weight for picking in batch.picking_ids
                    if picking.state != 'cancel'])

    @api.depends('picking_ids')
    def _compute_total_volume(self):
        for batch in self:
            for picking in batch.picking_ids:
                picking.action_calculate_volume()
            batch.total_volume = sum(
                [picking.volume for picking in batch.picking_ids
                    if picking.state != 'cancel'])

    @api.model
    def create(self, vals):
        if 'picking_ids' not in vals or vals.get(
                'carrier_id', False) is not False:
            return super().create(vals)
        carrier_ids = []
        for val in vals['picking_ids']:
            for picking_id in val[2]:
                picking = self.env['stock.picking'].browse(picking_id)
                carrier_ids.append(picking.carrier_id.id)
        if len(list(set(carrier_ids))) == 1:
            vals.update({
                'carrier_id': carrier_ids[0],
            })
        return super().create(vals)

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        for batch in self:
            for picking in batch.picking_ids:
                if picking.state not in ['done', 'cancel']:
                    picking.write({
                        'carrier_id': batch.carrier_id.id,
                    })

    def action_transfer(self):
        res = super().action_transfer()
        for batch in self:
            batch.write({
                'shipping_weight': batch.total_weight,
                'shipping_volume': batch.total_volume,
            })
        return res
