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
    carrier_tracking_ref = fields.Char(
        string='Carrier tracking reference',
    )
    carrier_price = fields.Float(
        string='Carrier price',
    )

    def create_simulate_stock_picking(self, picking_ids):
        partners = list(set(self.picking_ids.mapped('partner_id')))
        if len(partners) != 1:
            raise exceptions.ValidationError(
                _('Delivery: Different partners in the same group'))
        carriers = list(set(self.picking_ids.mapped('carrier_id')))
        if len(carriers) != 1:
            raise exceptions.ValidationError(
                _('Delivery: Different carriers in the same in group'))
        move_lines = []
        pickings = self.env['stock.picking'].browse(picking_ids)
        for move in pickings.mapped('move_lines').filtered(
                lambda ln: ln.state == 'done'):
            move_lines.append({
                'name': move.name,
                'product_id': move.product_id.id,
                'product_uom': move.product_uom.id,
                'product_uom_qty': move.quantity_done,
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

    def add_shipping_info(self, pickings, info):
        for picking in pickings:
            picking.write({
                'carrier_tracking_ref': info[0]['tracking_number'],
                'carrier_price': info[0]['exact_price'],
            })
        self.write({
            'carrier_tracking_ref': info[0]['tracking_number'],
            'carrier_price': info[0]['exact_price'],
            'shipping_weight': self.total_weight,
            'shipping_volume': self.total_volume,
        })
        return True

    def create_attachments(self, attachments):
        self.ensure_one()
        attachment_obj = self.env['ir.attachment']
        for attachment in attachments:
            attachment_obj.create({
                'name': attachment.name,
                'datas': attachment.datas,
                'datas_fname': attachment.datas_fname,
                'res_model': 'stock.picking.batch',
                'res_id': self.id,
                'mimetype': attachment.mimetype,
            })
        return True

    def done(self):
        context = self.env.context.copy()
        context['batch'] = self
        self.env.context = context
        picking_ids = self.get_pickings_to_validate()
        res = super().done()
        if not res:
            return res
        simulate_picking = self.create_simulate_stock_picking(picking_ids)
        info = simulate_picking.carrier_id.send_shipping(simulate_picking)
        self.create_attachments(self.get_picking_attachments(simulate_picking))
        self.add_shipping_info(self.picking_ids.filtered(
            lambda p: p.state == 'done' and p.id in picking_ids), info)
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

    def get_pickings_to_validate(self):
        picking_ids = []
        assigned_picking_list = self.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        for picking in assigned_picking_list:
            qty_request = sum(
                picking.move_ids_without_package.mapped('product_uom_qty'))
            qty_done = sum(
                picking.move_ids_without_package.mapped('quantity_done'))
            if qty_done == qty_request or (
                    qty_done != 0 and qty_done < qty_request):
                picking_ids.append(picking.id)
        return picking_ids

    def action_transfer(self):
        picking_ids = self.get_pickings_to_validate()
        res = super().action_transfer()
        if res:
            return res
        simulate_picking = self.create_simulate_stock_picking(picking_ids)
        info = simulate_picking.carrier_id.send_shipping(simulate_picking)
        self.create_attachments(self.get_picking_attachments(simulate_picking))
        self.add_shipping_info(self.picking_ids.filtered(
            lambda p: p.state == 'done' and p.id in picking_ids), info)
        simulate_picking.unlink()
        self.write({
            'shipping_weight': self.total_weight,
            'shipping_volume': self.total_volume,
        })
        return res
