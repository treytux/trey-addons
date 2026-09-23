###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockBarcodesRelocateLocation(models.TransientModel):
    _name = 'stock.barcodes.relocate.location'
    _description = 'Wizard to relocate complete location with barcodes'

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
        comodel_name='stock.barcodes.relocate.location.line',
        string='Picking lines',
        compute='_compute_line_ids',
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
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    step = fields.Integer(
        string='Wizard steps',
    )

    @api.depends('barcode')
    def _compute_line_ids(self):
        lines = self.env['stock.barcodes.relocate.location.line'].search([
            ('wizard_id', '=', self.id),
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
        lines = self.env['stock.barcodes.relocate.location.line'].search([])
        lines.unlink()
        return res

    def _set_message_info(self, message_type, message):
        self.message_type = message_type
        if self.barcode:
            self.message = _('Barcode: %s (%s)') % (self.barcode, message)
        else:
            self.message = '%s' % message

    def get_all_products_from_location(self, location_id):
        wizard_lines_obj = self.env['stock.barcodes.relocate.location.line']
        quants = self.env['stock.quant'].search([
            ('location_id', 'child_of', self.location_id.id),
            ('company_id', '=', self.env.user.company_id.id),
        ])
        for quant in quants:
            if quant.quantity <= 0:
                continue
            qty_res = self.env['stock.quant']._get_available_quantity(
                quant.product_id, quant.location_id, quant.lot_id)
            if qty_res <= 0:
                continue
            wizard_lines_obj.create({
                'wizard_id': self.id,
                'product_id': quant.product_id.id,
                'lot_id': quant.lot_id.id,
                'location_id': quant.location_id.id,
                'qty': qty_res,
                'quant_id': quant.id,
            })

    def show_picking_lines(self):
        if not self.location_id:
            raise ValidationError(
                _('No location origin asigned'))
        if not self.location_dest_id:
            raise ValidationError(
                _('No destination location asigned'))
        if self.location_id == self.location_dest_id:
            raise ValidationError(
                _('Source and destination location are the same'))
        self.get_all_products_from_location(self.location_id)
        self.step = 1
        return self._reopen_view()

    def process_barcode(self, barcode):
        location = self.env['stock.location'].search([
            ('barcode', '=', barcode),
        ])
        if len(location) == 1:
            if not self.location_id:
                self.location_id = location.id
                self._set_message_info('success', _('Barcode read correctly'))
                return
            else:
                self.location_dest_id = location.id
                self._set_message_info('success', _('Barcode read correctly'))
                return
        elif len(location) > 1:
            raise ValidationError(
                _('More than one location found %s') % (barcode))
        else:
            raise ValidationError(
                _('No location found with this barcode %s') % (barcode))
        return

    def check_quants_location(self):
        for line in self.line_ids:
            quant = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('lot_id', '=', line.lot_id.id),
                ('location_id', '=', line.location_id.id),
                ('quantity', '>=', line.qty),
                ('company_id', '=', self.env.user.company_id.id),
            ], limit=1)
            if not quant:
                return False
        return True

    @api.multi
    def validate_picking(self):
        if not self.check_quants_location():
            raise ValidationError(
                _('Error in the origin location of some line of the picking'))
        if len(self.line_ids) == 0:
            raise ValidationError(
                _('No lines to create picking to relocate complete location'))
        if not self.location_id:
            raise ValidationError(
                _('No location origin asigned'))
        if not self.location_dest_id:
            raise ValidationError(
                _('No destination location asigned'))
        if self.location_id == self.location_dest_id:
            raise ValidationError(
                _('Source and destination location are the same'))
        move_obj = self.env['stock.move']
        internal_picking_type = self.env.ref('stock.picking_type_internal')
        picking_id = self.env['stock.picking'].create({
            'partner_id': self.env.user.company_id.partner_id.id,
            'picking_type_id': internal_picking_type.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
        })
        msg = _(
            'Picking has been created with wizard for relocate complete '
            'location with barcode reader')
        picking_id.message_post(body=msg)
        for line in self.line_ids:
            move_obj.create({
                'name': line.product_id.name,
                'origin': line.quant_id.lot_id.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.qty,
                'picking_id': picking_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
        self.picking_id = picking_id.id
        self.step = 2
        if self.ids:
            return self._reopen_view()
        return

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
        self.process_barcode(barcode)
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


class StockBarcodesRelocateLocationLine(models.TransientModel):
    _name = 'stock.barcodes.relocate.location.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.barcodes.relocate.location',
        string='Wizard',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
    )
    qty = fields.Integer(
        string='Quantity',
    )
    quant_id = fields.Many2one(
        comodel_name='stock.quant',
        string='Quant',
    )
