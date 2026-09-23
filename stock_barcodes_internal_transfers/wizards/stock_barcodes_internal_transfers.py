###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockBarcodesInternalTransfers(models.TransientModel):
    _name = 'stock.barcodes.internal.transfers'
    _description = 'Wizard to create internal transfers with barcodes'

    _barcode_scanned = fields.Char(
        string='Barcode scanned',
        help='Last barcode scanned',
        store=False,
    )
    barcode = fields.Char(
        string='Barcode',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Current location',
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination location',
    )
    line_ids = fields.Many2many(
        comodel_name='stock.barcodes.internal.transfers.line',
        compute='_compute_line_ids',
        string='Wizard lines',
    )
    message_type = fields.Selection(
        selection=[
            ('info', 'Barcode read with additional info'),
            ('not_found', 'No barcode found'),
            ('more_match', 'More than one matches found'),
            ('success', 'Barcode read correctly'),
        ],
        readonly=True,
    )
    message = fields.Char(
        string='Message',
        readonly=True,
    )
    reference = fields.Char(
        string='Reference',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    picking_lines = fields.Many2many(
        comodel_name='stock.move.line',
        compute='_compute_picking_lines',
        string='Picking lines',
    )

    @api.depends('picking_id')
    def _compute_picking_lines(self):
        if self.picking_id:
            lines = self.env['stock.move.line'].search([
                ('picking_id', '=', self.picking_id.id),
            ])
            self.picking_lines = [(6, 0, lines.ids)]
        else:
            self.picking_lines = [(5, 0, 0)]

    @api.depends('barcode')
    def _compute_line_ids(self):
        lines = self.env['stock.barcodes.internal.transfers.line'].search([
            ('wizard_reference', '=', self.reference),
        ])
        self.line_ids = lines

    @api.onchange('_barcode_scanned')
    def _on_barcode_scanned(self):
        barcode = self._barcode_scanned
        if barcode:
            self._barcode_scanned = ''
            return self.on_barcode_scanned(barcode)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        lines = self.env['stock.barcodes.internal.transfers.line'].search([])
        lines.unlink()
        res['reference'] = datetime.now().strftime('%Y%m%d%H%M%S')
        return res

    def _set_messagge_info(self, message_type, message):
        self.message_type = message_type
        if self.barcode:
            self.message = _('Barcode: %s (%s)') % (self.barcode, message)
        else:
            self.message = '%s' % message

    def play_sounds(self, sound):
        if isinstance(self.id, int):
            channel = 'barcodes_internal_transfers_sound-%s' % self.id
        else:
            channel = 'barcodes_internal_transfers_sound-%s' % self._origin.id
        if sound == 'ok':
            self.env['bus.bus']._sendone(
                channel, 'Sound ok message', {
                    'sound': 'ok',
                    'partner_id': self.env.user.partner_id.id,
                }
            )
        elif sound == 'error':
            self.env['bus.bus']._sendone(
                channel, 'Sound error message', {
                    'sound': 'error',
                    'partner_id': self.env.user.partner_id.id,
                }
            )

    def identify_barcode(self, barcode):
        wizard_lines_obj = self.env['stock.barcodes.internal.transfers.line']
        lot_id = self.env['stock.lot'].search([
            ('name', '=', barcode),
        ])
        if len(lot_id) == 1:
            exists_lot = wizard_lines_obj.search([
                ('lot_id', '=', lot_id.id),
            ])
            if exists_lot:
                raise ValidationError(
                    _('The batch/serial %s number exists in picking') % (
                        barcode))
            quants = lot_id.quant_ids.filtered(
                lambda q: q.location_id.usage == 'internal' and q.quantity > 0)
            if not quants:
                raise ValidationError(
                    _('No stock for product %s in internal locations') % (
                        barcode))
            if len(quants) > 1:
                raise ValidationError(
                    _('Product stock %s in more than one internal location') %
                    (barcode))
            qty_available = self.env['stock.quant']._get_available_quantity(
                quants[0].product_id, quants[0].location_id, lot_id)
            if qty_available <= 0:
                raise ValidationError(
                    _('There is no available quantity in quant or all units of'
                      ' lot [%s] are reserved.') % quants[0].lot_id.name)
                return
            wizard_lines_obj.create({
                'wizard_id': self._origin.id,
                'barcode': barcode,
                'product_id': lot_id.product_id.id,
                'lot_id': lot_id.id,
                'location_id': quants[0].location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'wizard_reference': self.reference,
                'qty': 1,
            })
            self.play_sounds('ok')
            self._set_messagge_info('success', _('Barcode read correctly'))
            return
        location = self.env['stock.location'].search([
            ('barcode', '=', barcode),
        ])
        if len(location) == 1:
            self.location_dest_id = location.id
            self.env['stock.barcodes.internal.transfers.line'].search([
                ('wizard_reference', '=', self.reference),
            ]).write({
                'location_dest_id': location.id,
            })
            for line in self.line_ids:
                line.location_dest_id = location.id
            self._set_messagge_info('success', _('Barcode read correctly'))
            self.play_sounds('ok')
            return
        if len(location) > 1:
            raise ValidationError(
                _('More than one location found %s') % (barcode))
        picking_type = self.env['stock.picking.type'].search([
            ('validate_barcode_action', '=', barcode),
        ], limit=1)
        if len(picking_type) == 1:
            if not self.location_dest_id:
                raise ValidationError(
                    _('Not destination location asigned %s') % (barcode))
            if len(self.line_ids) == 0:
                raise ValidationError(
                    _('No lines to create picking internal transfers'))
            self.validate_picking(picking_type)
            return
        if len(picking_type) > 1:
            raise ValidationError(
                _('More than one operation code found %s') % (barcode))
        self._set_messagge_info('not_found', _('Barcode not found'))
        self.play_sounds('error')
        raise ValidationError(_('Barcode %s not found' % barcode))

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
        self.identify_barcode(barcode)
        return

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def check_quants_location(self):
        for line in self.line_ids:
            quant = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('lot_id', '=', line.lot_id.id),
                ('location_id', '=', line.location_id.id),
                ('quantity', '>=', line.qty),
                ('company_id', '=', self.env.company.id),
            ], limit=1)
            if not quant:
                return False
        return True

    def validate_picking(self, picking_type=None):
        if not self.check_quants_location():
            raise ValidationError(
                _('Error in the origin location of some line of the picking'))
        if len(self.line_ids) == 0:
            raise ValidationError(
                _('No lines to create picking internal transfers'))
            return
        if not self.line_ids.mapped('location_dest_id'):
            raise ValidationError(
                _('Not destination location asigned'))
            return
        if isinstance(picking_type, dict) and 'active_id' in picking_type:
            picking_type = self.env['stock.picking.type'].browse(
                picking_type['active_id'])
        if not picking_type and self.env.context.get('active_id'):
            picking_type = self.env['stock.picking.type'].browse(
                self.env.context['active_id'])
        if not picking_type:
            raise ValidationError(
                _('No picking type found to create picking'))
        picking = self.env['stock.picking'].create({
            'partner_id': picking_type.partner_internal_transfers.id or False,
            'picking_type_id': picking_type.id,
            'location_id': self.line_ids[0].location_id.id,
            'location_dest_id': self.line_ids.mapped('location_dest_id').id,
        })
        msg = _(
            'Picking has been created with wizard for internal transfers with '
            'barcode scanning')
        picking.message_post(body=msg)
        move_line_group = []
        for line in self.line_ids:
            move = picking.move_ids.create({
                'name': line.product_id.name,
                'origin': line.barcode,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.qty,
                'picking_id': picking.id,
                'location_id': line.location_id.id,
                'location_dest_id': line.location_dest_id.id,
            })
            move_line_group.append([move, line])
        picking.action_confirm()
        picking.action_assign()
        for move, line in move_line_group:
            move.move_line_ids.location_id = line.location_id.id
            move.move_line_ids.lot_id = line.lot_id.id
            move.move_line_ids.qty_done = line.qty
        picking.button_validate()
        self._set_messagge_info('success', _('Picking validate correctly'))
        self.play_sounds('ok')
        self.picking_id = picking.id
        if self.ids:
            return self._reopen_view()
        return


class StockBarcodesInternalTransfersLine(models.TransientModel):
    _name = 'stock.barcodes.internal.transfers.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.barcodes.internal.transfers',
        string='Wizard',
    )
    barcode = fields.Char(
        string='Barcode',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Current location',
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination location',
    )
    qty = fields.Integer(
        string='Quantity',
    )
    wizard_reference = fields.Char(
        string='Wizard reference',
    )
    stock_info = fields.Char(
        string='Stock info',
        compute='_compute_stock_info',
    )

    @api.depends('product_id')
    def _compute_stock_info(self):
        stock_location_obj = self.env['stock.location']
        for line in self:
            if not line.product_id:
                line.stock_info = ''
                continue
            domain = [
                ('product_id', '=', line.product_id.id),
                ('location_id.usage', '=', 'internal'),
                ('location_id', '!=', line.location_id.id),
            ]
            quants = self.env['stock.quant'].read_group(
                domain, ['location_id', 'quantity'], ['location_id'])
            location_stock = dict([(
                stock_location_obj.browse(data['location_id'][0]).name,
                data['quantity']) for data in quants])
            location_stock = dict(sorted(
                location_stock.items(), key=lambda x: x[1], reverse=True))
            location_stock = dict(list(location_stock.items())[:5])
            stock_info = [
                f'{location}: {quantity}'
                for location, quantity in location_stock.items()]
            line.stock_info = ','.join(stock_info)
