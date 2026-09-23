###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError


class StockBarcodesDummyLabel(models.TransientModel):
    _name = 'stock.barcodes.dummy.label'
    _description = 'Wizard to create outgoing pickings with dummy labels'

    _barcode_scanned = fields.Char(
        string='Barcode scanned',
        help='Last barcode scanned',
        store=False,
    )
    barcode = fields.Char(
        string='Barcode',
    )
    line_ids = fields.Many2many(
        comodel_name='stock.barcodes.dummy.label.line',
        string='Picking lines',
    )
    confirm_line_ids = fields.One2many(
        comodel_name='stock.barcodes.dummy.confirm',
        string='Confirmed picking lines',
        inverse_name='wizard_id',
    )
    reorganize_line_ids = fields.Many2many(
        comodel_name='stock.barcodes.reorganize.line',
        string='Reorganize lines',
    )
    message_type = fields.Selection(
        selection=[
            ('info', 'Barcode read with additional info'),
            ('not_found', 'No barcode found'),
            ('more_match', 'More than one matches found'),
            ('success', 'Barcode read correctly'),
            ('error', 'Barcode reading error')
        ],
        readonly=True,
    )
    message = fields.Text(
        string='Message',
        readonly=True,
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    partner_id = fields.Many2one(
        related='picking_id.partner_id',
        string='Partner',
    )
    partner_ref = fields.Char(
        related='partner_id.ref',
        string='Partner internal reference',
    )
    is_packaging = fields.Boolean(
        string='Is packaging',
    )
    package_barcode = fields.Char(
        string='Package barcode',
    )
    reorganize_packages = fields.Boolean(
        string='Reorganize packages',
    )
    pallet_mode = fields.Selection(
        selection=[
            ('complete_empty_mode', 'Complete empty mode'),
            ('individual_mode', 'Individual mode'),
        ],
        string='Pallet read mode',
        default='complete_empty_mode',
    )
    pallet_barcode = fields.Char(
        string='Pallet barcode',
    )
    partner_address = fields.Char(
        string='Address',
    )
    product_qty = fields.Integer(
        string='Product qty',
        default=1,
    )
    product_packaging = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )

    def get_line_ids(self):
        lines = self.env['stock.barcodes.dummy.label.line'].search([
            ('wizard_id', '=', self._origin.id),
        ])
        self.line_ids = lines

    def get_confirm_line_ids(self):
        lines = self.env['stock.barcodes.dummy.confirm'].search([
            ('wizard_id', '=', self._origin.id),
        ])
        self.confirm_line_ids = lines

    def get_reorganize_line_ids(self):
        lines = self.env['stock.barcodes.reorganize.line'].search([
            ('wizard_id', '=', self._origin.id),
        ])
        self.reorganize_line_ids = lines

    @api.onchange('_barcode_scanned')
    def _on_barcode_scanned(self):
        barcode = self._barcode_scanned
        if barcode:
            self._barcode_scanned = ''
            return self.on_barcode_scanned(barcode)

    def play_sounds(self, sound):
        if isinstance(self.id, int):
            channel = 'barcodes_dummy_label_sound-%s' % self.id
        else:
            channel = 'barcodes_dummy_label_sound-%s' % self._origin.id
        if sound == 'ok':
            self.env['bus.bus'].sendone(
                channel, {
                    'sound': 'ok',
                    'partner_id': self.env.user.partner_id.id,
                },
            )
        elif sound == 'error':
            self.env['bus.bus'].sendone(
                channel, {
                    'sound': 'error',
                    'partner_id': self.env.user.partner_id.id,
                },
            )

    def _set_messagge_info(self, message_type, message):
        self.message_type = message_type
        if message_type == 'error' or message_type == 'not_found':
            self.play_sounds('error')
        elif message_type == 'success':
            self.play_sounds('ok')
        if self.barcode:
            self.message = _('Barcode: %s (%s)') % (self.barcode, message)
        else:
            self.message = '%s' % message

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
        self.get_line_ids()
        self.get_confirm_line_ids()
        self.get_reorganize_line_ids()
        self.identify_barcode(barcode)
        self.get_line_ids()
        self.get_confirm_line_ids()
        self.get_reorganize_line_ids()
        return

    def there_quants_in_lot(self, ml, qty, lot, barcode=None):
        try:
            qty_available = ml.product_id.with_context(
                location=ml.location_id.id,
                lot_id=lot.id
            ).qty_available
            if qty_available < qty:
                lot_info = lot.name if lot else 'No lot'
                raise UserError(_(
                    'Box: %s, Insufficient stock: %s in %s location. '
                    'Lot: %s. Available: %s, Required: %s') % (
                        barcode or '',
                        ml.product_id.display_name,
                        ml.location_id.complete_name, lot_info,
                        qty_available, qty)
                )
        except Exception as e:
            if not isinstance(e, UserError):
                raise UserError(_('Error checking stock: %s') % (str(e)))
            raise

    def assing_dummy_in_moves(self, moves, barcode):
        dummy = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcode)
        if not dummy:
            return False, False
        qty = (dummy.packaging_id and dummy.packaging_id.qty or 1)
        move_lines = moves.mapped('move_line_ids').filtered(
            lambda ml: (
                ml.product_id == dummy.product_id
                and not ml.result_package_id
                and ml.qty_done == 0
            )
        )
        if not move_lines:
            return dummy, False
        ml = move_lines[0]
        if ml.product_id.tracking != 'none':
            self.there_quants_in_lot(ml, qty, dummy.lot_id or False, barcode)
        ml.write({
            'qty_done': qty,
            'lot_id': dummy.lot_id.id or False,
        })
        pack = self.picking_id.put_in_pack()
        if isinstance(pack, dict):
            pack_id = pack.get(
                'context', False).get('default_stock_quant_package_id')
            pack = self.env['stock.quant.package'].browse(pack_id)
        pack.write({
            'name': barcode,
            'dummy_id': dummy.id,
        })
        return dummy, move_lines[0]

    def get_dummy_type(self, dummy_type):
        return self.env['stock.quant_package.dummy.type'].search([
            ('dummy_type', '=', dummy_type),
        ])

    def check_packages_in_containers(self):
        box_to_containers = {}
        for line in self.confirm_line_ids:
            containers = box_to_containers.setdefault(line.barcode, set())
            containers.add(line.pallet_barcode)
        for box, containers in box_to_containers.items():
            if len(containers) > 1:
                raise ValidationError(
                    _('Lines with same box ("%s") must have same container. '
                      'Currently found: %s') % (
                          box, ', '.join(c or _('[empty]') for c in containers))
                )

    def button_validate_dummy_scan(self):
        self.check_packages_in_containers()
        dummy_type = self.get_dummy_type('dummy')
        mixed_type = self.get_dummy_type('mixed_package')
        dummy_barcodes = self.confirm_line_ids.filtered(
            lambda ln: ln.barcode.startswith(
                dummy_type.prefix)).mapped('barcode')
        for barcode in dummy_barcodes:
            line = self.confirm_line_ids.filtered(
                lambda ln: ln.barcode == barcode)
            res_config = self.env['res.config.settings']
            if res_config.is_force_pallet_barcode_active():
                if not line.pallet_barcode:
                    raise ValidationError(
                        _('Must include pallet barcode on package %s') % (
                            line.barcode))
            if not line.lot_id and line.product_id.tracking != 'none':
                raise ValidationError(
                    _('Must include lot/serial number on package %s') % (
                        line.barcode))
            self.validate_dummy_barcodes(barcode)
        mixed_barcodes = self.confirm_line_ids.filtered(
            lambda ln: ln.barcode.startswith(
                mixed_type.prefix)).mapped('barcode')
        mixed_barcodes = list(set(mixed_barcodes))
        for barcode in mixed_barcodes:
            lines = self.confirm_line_ids.filtered(
                lambda ln: ln.barcode == barcode)
            pckgs = self.picking_id.move_line_ids.mapped(
                'result_package_id').filtered(lambda p: p.name == barcode)
            for line in lines:
                res_config = self.env['res.config.settings']
                if res_config.is_force_pallet_barcode_active():
                    if not line.pallet_barcode:
                        raise ValidationError(
                            _('Must include pallet barcode on package %s') % (
                                line.barcode))
                if not line.lot_id and line.product_id.tracking != 'none':
                    raise ValidationError(
                        _('Must include lot/serial number on package %s') % (
                            line.barcode))

                move_lines = self.picking_id.move_line_ids.filtered(
                    lambda ln: ln.product_id == line.product_id)
                if not move_lines:
                    raise ValidationError(_('No stock lines to be realised'))
                if pckgs:
                    pckgs = self.picking_id.move_line_ids.mapped(
                        'result_package_id').filtered(
                        lambda p: p.name == barcode)
                    new_ml = move_lines[0].copy()
                    new_ml.write({
                        'product_uom_qty': line.qty,
                        'qty_done': line.qty,
                        'result_package_id': pckgs[0].id,
                    })
                    move_lines[0].write({
                        'product_uom_qty': (
                            move_lines[0].product_uom_qty - line.qty),
                        'qty_done': 0,
                    })
                else:
                    if line.lot_id:
                        self.there_quants_in_lot(
                            move_lines[0], line.qty, line.lot_id or False, barcode)
                    move_lines[0].write({
                        'qty_done': line.qty,
                        'lot_id': line.lot_id.id if line.lot_id else False
                    })
            if not pckgs:
                package = self.picking_id.put_in_pack()
                if isinstance(package, dict):
                    package_id = package.get(
                        'context', False).get('default_stock_quant_package_id')
                    package = self.env['stock.quant.package'].browse(package_id)
                package.name = barcode
        pallet_lines = self.confirm_line_ids.filtered(
            lambda ln: ln.pallet_barcode)
        packages = self.picking_id.mapped(
            'move_lines.move_line_ids.result_package_id')
        for line in pallet_lines:
            package_pallet = self.env['stock.quant.package'].search([
                ('name', '=', line.pallet_barcode),
            ])
            if not package_pallet:
                package_pallet = self.env['stock.quant.package'].create({
                    'name': line.pallet_barcode,
                })
            for package in packages.filtered(lambda p: p.name == line.barcode):
                package.parent_id = package_pallet.id
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', self.picking_id.id),
        ])
        logs.write({'active': False})

    def button_reorganize_packages(self):
        barcodes = self.reorganize_line_ids.mapped('pallet_barcode')
        for barcode in barcodes:
            lines = self.confirm_line_ids.filtered(
                lambda ln: ln.pallet_barcode == barcode)
            lines.write({'pallet_barcode': ''})
        for line in self.reorganize_line_ids:
            confirm_lines = self.confirm_line_ids.filtered(
                lambda ln: line.package_barcode == ln.barcode)
            confirm_lines.write({'pallet_barcode': line.pallet_barcode})
        self.reorganize_packages = False
        for line in self.line_ids:
            moves = self.picking_id.move_lines.filtered(
                lambda m: m.product_id == line.product_id)
            qty_res = sum(moves.mapped('product_uom_qty')) - sum(
                moves.mapped('quantity_done'))
            confirm_lines = self.confirm_line_ids.filtered(
                lambda ln: ln.product_id == line.product_id)
            line.qty = qty_res - sum(confirm_lines.mapped('qty'))
        self.reorganize_line_ids = [(6, 0, [])]
        self.update_line_log()
        lines = self.env['stock.barcodes.reorganize.line'].search([
            ('wizard_id', '=', self.id),
        ])
        lines.unlink()
        return self._reopen_view()

    @api.onchange('reorganize_packages')
    def _onchange_reorganize_packages(self):
        self.reorganize_line_ids = [(6, 0, [])]
        lines = self.env['stock.barcodes.reorganize.line'].search([
            ('wizard_id', '=', self.id),
        ])
        lines.unlink()
        self.pallet_barcode = ''
        self.message = ''
        self.message_type = 'more_match'

    def read_reorganize_barcodes(self, barcode):
        if not self._origin.confirm_line_ids:
            self._set_messagge_info(
                'error', _('Nothing to reorganize, no read made'))
            return
        dummy_obj = self.env['stock.quant.package_dummy']
        dummy = dummy_obj.search_from_barcode(barcode)
        if len(dummy) > 1:
            self._set_messagge_info('error', _('Duplicate dummy'))
            return
        elif not dummy:
            self._set_messagge_info(
                'error', _('Barcode not related to box or pallet'))
            return
        dummy_type = self.get_dummy_type('dummy')
        pallet_type = self.get_dummy_type('pallet')
        mixed_type = self.get_dummy_type('mixed_package')
        if self._origin.pallet_barcode or self.pallet_barcode:
            if barcode.startswith(dummy_type.prefix):
                if barcode in self._origin.reorganize_line_ids.mapped(
                        'package_barcode'):
                    self._set_messagge_info(
                        'error', _('The same box cannot be assigned twice'))
                    return
                if barcode in self._origin.confirm_line_ids.mapped('barcode'):
                    self.env['stock.barcodes.reorganize.line'].create({
                        'wizard_id': self._origin.id,
                        'pallet_barcode': self.pallet_barcode or (
                            self._origin.package_barcode),
                        'package_barcode': barcode,
                    })
                    self._set_messagge_info('success', _('Box read correctly'))
                    return
            elif barcode.startswith(mixed_type.prefix):
                if barcode in self._origin.reorganize_line_ids.mapped(
                        'package_barcode'):
                    self._set_messagge_info(
                        'error', _('The same box cannot be assigned twice'))
                    return
                if barcode in self._origin.confirm_line_ids.mapped('barcode'):
                    self.env['stock.barcodes.reorganize.line'].create({
                        'wizard_id': self._origin.id,
                        'pallet_barcode': self.pallet_barcode or (
                            self._origin.package_barcode),
                        'package_barcode': barcode,
                    })
                    self._set_messagge_info('success', _('Box read correctly'))
                    return
            elif barcode.startswith(pallet_type.prefix):
                if self._origin.pallet_barcode == barcode or (
                        self.pallet_barcode == barcode):
                    self.pallet_barcode = ''
                    self._set_messagge_info('success', _('Pallet closed'))
                    return
                else:
                    self._set_messagge_info(
                        'error', _('You have to close the pallet '
                                   'by reading its barcode'))
                    return
        if barcode.startswith(pallet_type.prefix):
            self.pallet_barcode = barcode
            self._origin.pallet_barcode = barcode
            self._set_messagge_info('success', _('Pallet read correctly'))
            return
        else:
            self._set_messagge_info(
                'error', _('You must first enter a barcode from a pallet'))
            return

    def identify_barcode(self, barcode):
        if self._origin.reorganize_packages or self.reorganize_packages:
            return self.read_reorganize_barcodes(barcode)
        if self.pallet_barcode:
            context = self.env.context.copy()
            context['pallet_barcode'] = self.pallet_barcode
            self.env.context = context
        dummy_obj = self.env['stock.quant.package_dummy']
        dummy = dummy_obj.search_from_barcode(barcode)
        mixed_type = self.get_dummy_type('mixed_package')
        dummy_validated = self.env['stock.move.line'].search([
            ('result_package_id.name', '=', barcode)
        ])
        if dummy_validated:
            picking_id = dummy_validated[0].picking_id.id
            if (barcode.startswith(mixed_type.prefix)
                    and picking_id == self.picking_id.id):
                pass
            else:
                self._set_messagge_info(
                    'error',
                    _('Barcode %s already validated in picking %s') % (
                        barcode, dummy_validated[0].picking_id.name))
                return
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('active', '=', True),
            ('picking_id', '!=', self.picking_id.id),
            '|',
            ('barcode', '=', barcode),
            ('pallet_barcode', '=', barcode),
        ])
        if logs:
            self._set_messagge_info(
                'error',
                _('Barcode %s is already in use in the picking %s') % (
                    barcode, logs[0].picking_id.name))
            return
        qty_requested = sum(
            self.picking_id.move_lines.mapped('product_uom_qty'))
        qty_done = sum(self._origin.confirm_line_ids.mapped('qty'))
        if self.is_packaging or self._origin.is_packaging:
            product = self.env['product.product'].search([
                ('barcode', '=', barcode),
            ])
            if len(product) > 1:
                self._set_messagge_info(
                    'error', _('Mulitple products found for the same barcode'))
                return
            if not product:
                if self.package_barcode == barcode or (
                        self._origin.package_barcode == barcode):
                    self._origin.write({
                        'is_packaging': False,
                        'package_barcode': '',
                    })
                    self._origin.is_packaging = False
                    self._origin.package_barcode = ''
                    self.is_packaging = False
                    self.package_barcode = ''
                    self.product_packaging = False
                    self._set_messagge_info('success', _('Closed mixed box'))
                    return
                mixed_type = self.get_dummy_type('mixed_package')
                if barcode.startswith(mixed_type.prefix):
                    self._origin.write({
                        'is_packaging': True,
                        'package_barcode': barcode,
                    })
                    self._origin.is_packaging = True
                    self._origin.package_barcode = barcode
                    self.is_packaging = True
                    self.package_barcode = barcode
                    self.product_packaging = False
                    return
                pallet_type = self.get_dummy_type('pallet')
                if barcode.startswith(pallet_type.prefix):
                    self._origin.write({
                        'is_packaging': False,
                        'package_barcode': '',
                    })
                    self._origin.is_packaging = False
                    self._origin.package_barcode = ''
                    self.is_packaging = False
                    self.package_barcode = ''
                    self.product_packaging = False
                    context = self.env.context.copy()
                    context['pallet_barcode'] = barcode
                    self.env.context = context
                    self.pallet_barcode = barcode
                    if self.ids:
                        self.write({
                            'pallet_barcode': barcode,
                        })
                    self._origin.pallet_barcode = barcode
                    self._origin.write({
                        'pallet_barcode': barcode,
                    })
                    self._set_messagge_info(
                        'success', _('Continue reading boxes in pallet'))
                    return
                self._set_messagge_info(
                    'error', _('Product barcode not found. You have to enter a '
                               'barcode of a product or close the mixed box'))
                return
            line = self._origin.line_ids.filtered(
                lambda ln: ln.product_id == product)
            if not line:
                self._set_messagge_info(
                    'error', _('Product not belongs to picking'))
                return
            if qty_done >= qty_requested:
                self._set_messagge_info('error', _('No quantity left to serve'))
                return
            if line.qty == 0:
                self._set_messagge_info('error', _('No quantity left to serve'))
                return
            line.qty = line.qty - 1
            dummy_package = dummy_obj.search_from_barcode(
                self.package_barcode or self._origin.package_barcode)
            confirm_line = self.env['stock.barcodes.dummy.confirm'].create({
                'wizard_id': self._origin.id,
                'barcode': self.package_barcode or self._origin.package_barcode,
                'product_id': product.id,
                'dummy_id': dummy_package.id,
                'qty': 1,
            })
            if self.pallet_barcode:
                confirm_line.pallet_barcode = self.pallet_barcode
            self._origin.write({
                'confirm_line_ids': [(4, confirm_line.id)],
            })
            self.product_packaging = product.id
            self._set_messagge_info(
                'success', _('Barcode read correctly. You can enter another '
                             'barcode for a product or close the box'))
            return self.update_line_log()
        if len(dummy) > 1:
            self._set_messagge_info('error', _('Duplicate dummy'))
            return
        if len(dummy) == 1:
            dummy_type = self.get_dummy_type('dummy')
            pallet_type = self.get_dummy_type('pallet')
            mixed_type = self.get_dummy_type('mixed_package')
            if barcode.startswith(dummy_type.prefix):
                repeat_lines = self.confirm_line_ids.filtered(
                    lambda ln: ln.barcode == barcode)
                if repeat_lines and not self.pallet_barcode:
                    return
                if self.pallet_barcode and (
                        self.pallet_mode == 'individual_mode'):
                    lines = self.confirm_line_ids.filtered(
                        lambda ln: ln.barcode == barcode)
                    if not lines:
                        if qty_done >= qty_requested:
                            self._set_messagge_info(
                                'error', _('No quantity left to serve'))
                            return
                        line = self._origin.line_ids.filtered(
                            lambda ln: ln.product_id == dummy.product_id)
                        dummy_qty = dummy.packaging_id and (
                            dummy.packaging_id.qty or 1)
                        if line.qty == 0:
                            self._set_messagge_info(
                                'error', _('No quantity left to serve'))
                            return
                        if line.qty - dummy.qty < 0:
                            self._set_messagge_info(
                                'error', _('The box contains more than the '
                                           'remaining quantity'))
                            return
                        wizard = self.env['stock.package_dummy.read'].create({
                            'location_id': self.picking_id.location_id.id,
                            'action': 'stock_picking',
                            'picking_id': self.picking_id.id,
                            'barcodes': barcode,
                        })
                        wizard.action_simulate()
                        if wizard.line_ids:
                            error_list = 'n'.join(
                                line.name for line in wizard.line_ids)
                            self._set_messagge_info('error', error_list)
                            return
                        line.qty = line.qty - (
                            dummy.packaging_id and dummy.packaging_id.qty or 1)
                        confirm_line_obj = (
                            self.env['stock.barcodes.dummy.confirm'])
                        qty = dummy.packaging_id and dummy.packaging_id.qty or 1
                        confirm_line = confirm_line_obj.create({
                            'wizard_id': self._origin.id,
                            'barcode': barcode,
                            'product_id': dummy.product_id.id,
                            'lot_id': dummy.lot_id.id,
                            'qty': qty,
                            'dummy_id': dummy.id,
                            'pallet_barcode': self.pallet_barcode,
                        })
                        self._origin.write({
                            'confirm_line_ids': [(4, confirm_line.id)],
                        })
                        self._set_messagge_info(
                            'success', _('Dummy barcode read correctly'))
                        return self.update_line_log()
                    for line in lines:
                        line.pallet_barcode = self.pallet_barcode
                    self._set_messagge_info(
                        'success', _('Box assigned to pallet'))
                    return self.update_line_log()
                if qty_done >= qty_requested:
                    self._set_messagge_info(
                        'error', _('No quantity left to serve'))
                    return
                line = self._origin.line_ids.filtered(
                    lambda ln: ln.product_id == dummy.product_id)
                dummy_qty = dummy.packaging_id and dummy.packaging_id.qty or 1
                if line.qty == 0:
                    self._set_messagge_info(
                        'error', _('No quantity left to serve'))
                    return
                if line.qty - dummy_qty < 0:
                    self._set_messagge_info(
                        'error', _('The box contains more than the '
                                   'remaining quantity'))
                    return
                wizard = self.env['stock.package_dummy.read'].create({
                    'location_id': self.picking_id.location_id.id,
                    'action': 'stock_picking',
                    'picking_id': self.picking_id.id,
                    'barcodes': barcode,
                })
                wizard.action_simulate()
                if wizard.line_ids:
                    error_list = '\n'.join(
                        line.name for line in wizard.line_ids)
                    self._set_messagge_info('error', error_list)
                    return
                line.qty = line.qty - (
                    dummy.packaging_id and dummy.packaging_id.qty or 1)
                confirm_line_obj = self.env['stock.barcodes.dummy.confirm']
                confirm_line = confirm_line_obj.create({
                    'wizard_id': self._origin.id,
                    'barcode': barcode,
                    'product_id': dummy.product_id.id,
                    'lot_id': dummy.lot_id.id,
                    'qty': (
                        dummy.packaging_id and dummy.packaging_id.qty or 1),
                    'dummy_id': dummy.id,
                })
                self._origin.write({
                    'confirm_line_ids': [(4, confirm_line.id)],
                })
                self._set_messagge_info(
                    'success', _('Dummy barcode read correctly'))
                return self.update_line_log()
            elif barcode.startswith(pallet_type.prefix):
                context = self.env.context.copy()
                context['pallet_barcode'] = barcode
                self.env.context = context
                if self.pallet_mode == 'complete_empty_mode':
                    confirm_lines = self.confirm_line_ids.filtered(
                        lambda ln: not ln.pallet_barcode)
                    for line in confirm_lines:
                        line.pallet_barcode = barcode
                    self._set_messagge_info(
                        'success', _('Barcode read correctly. This pallet has '
                                     'been assigned to all boxes that not '
                                     'have pallet'))
                    return self.update_line_log()
                else:
                    if self.pallet_barcode:
                        self._set_messagge_info(
                            'success', _('Barcode read. Pallet closed'))
                        self.pallet_barcode = ''
                        return
                    self.pallet_barcode = barcode
                    self._set_messagge_info(
                        'success', _('Barcode read correctly. The next barcode '
                                     'must be a box'))
                    return
            elif barcode.startswith(mixed_type.prefix):
                if self.pallet_barcode and (
                        self.pallet_mode == 'individual_mode'):
                    lines = self.confirm_line_ids.filtered(
                        lambda ln: ln.barcode == barcode)
                    for line in lines:
                        line.pallet_barcode = self.pallet_barcode
                    self._origin.write({
                        'is_packaging': True,
                        'package_barcode': barcode,
                    })
                    self._origin.is_packaging = True
                    self.is_packaging = True
                    self._origin.package_barcode = barcode
                    self._set_messagge_info(
                        'success', _('Barcode read correctly. The following '
                                     'barcode must be a product barcode'))
                    return
                if qty_done >= qty_requested:
                    self._set_messagge_info(
                        'error', _('No quantity left to serve'))
                    return
                self._origin.write({
                    'is_packaging': True,
                    'package_barcode': barcode,
                })
                self._origin.is_packaging = True
                self.is_packaging = True
                self._origin.package_barcode = barcode
                self._set_messagge_info(
                    'success', _('Barcode read correctly. The following barcode'
                                 ' must be a product barcode'))
                return
        product = self.env['product.product'].search([
            ('barcode', '=', barcode),
        ])
        if product:
            self._set_messagge_info(
                'error', _('To put a product in a box, '
                           'you must first read the box code'))
            return
        self._set_messagge_info('not_found', _('Barcode not found'))
        return

    def validate_dummy_barcodes(self, barcode):
        if not self.picking_id:
            raise exceptions.UserError(_('Launch this wizard from picking'))
        moves = self.picking_id.move_lines
        dummy, move_line = self.assing_dummy_in_moves(moves, barcode)
        if not move_line:
            need_products = moves.filtered(
                lambda m: dummy.product_id == m.product_id)
            if need_products:
                raise exceptions.ValidationError(_(
                    'Barcode %s not generate move line.\n'
                    'You introduce more quantity than necesary of '
                    'product "%s"') % (barcode, dummy.product_id.name))
            raise exceptions.ValidationError(_(
                'Barcode %s not generate move line.\n'
                'Product "%s" is not necesary for this picking.') % (
                    barcode, dummy.product_id.name))
        return True

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

    def action_update_qty_line(self):
        confirm_line = self.confirm_line_ids[-1]
        confirm_line.qty = self.product_qty
        moves = self.picking_id.move_lines.filtered(
            lambda m: m.product_id == confirm_line.product_id)
        qty_res = sum(moves.mapped('product_uom_qty')) - sum(
            moves.mapped('quantity_done'))
        wizard_line = self.line_ids.filtered(
            lambda ln: ln.product_id == confirm_line.product_id)
        product_lines = self.confirm_line_ids.filtered(
            lambda ln: ln.product_id == confirm_line.product_id)
        new_qty_res = qty_res - sum(product_lines.mapped('qty'))
        if new_qty_res < 0:
            confirm_line.qty = 1
            self.is_packaging = False
            self.package_barcode = ''
            self.product_qty = 1
            self.product_packaging = False
            self._set_messagge_info(
                'error', _('Selected qty exceeds requested qty in picking'))
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.barcodes.dummy.label',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': {},
            }
        wizard_line.qty = new_qty_res
        self.is_packaging = True
        self.product_qty = 1
        self.product_packaging = False
        lines = self.line_ids.filtered(lambda ln: ln != wizard_line)
        for line in lines:
            confirm_lines = self.confirm_line_ids.filtered(
                lambda ln: ln.product_id == line.product_id)
            qty_confirm = sum(confirm_lines.mapped('qty'))
            moves = self.picking_id.move_lines.filtered(
                lambda m: m.product_id == line.product_id)
            qty_res = sum(moves.mapped('product_uom_qty')) - sum(
                moves.mapped('quantity_done'))
            line.qty = qty_res - qty_confirm
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', self.picking_id.id),
        ])
        count = 0
        for line in self.confirm_line_ids:
            line.pallet_barcode = logs[count].pallet_barcode
            count += 1
        self.update_line_log()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.barcodes.dummy.label',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {},
        }

    def update_line_log(self):
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', self.picking_id.id),
        ])
        logs.write({'active': False})
        if hasattr(self, '_origin'):
            confirm_lines = self._origin.confirm_line_ids
        else:
            confirm_lines = self.confirm_line_ids
        for line in confirm_lines:
            self.env['stock.barcodes.dummy.log'].create({
                'picking_id': self.picking_id.id,
                'barcode': line.barcode,
                'product_id': line.product_id.id,
                'lot_id': line.lot_id and line.lot_id.id or False,
                'qty': line.qty,
                'dummy_id': line.dummy_id.id,
                'pallet_barcode': line.pallet_barcode,
                'active': True,
            })
        return


class StockBarcodesDummyLabelLine(models.TransientModel):
    _name = 'stock.barcodes.dummy.label.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.barcodes.dummy.label',
        string='Wizard',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    default_code = fields.Char(
        related='product_id.default_code',
    )
    qty = fields.Integer(
        string='Pending quantity',
    )


class StockBarcodesReorganizeLine(models.TransientModel):
    _name = 'stock.barcodes.reorganize.line'
    _description = 'Reorganize lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.barcodes.dummy.label',
        string='Wizard',
    )
    pallet_barcode = fields.Char(
        string='Pallet',
    )
    package_barcode = fields.Char(
        string='Box',
    )


class StockBarcodesDummyConfirm(models.TransientModel):
    _name = 'stock.barcodes.dummy.confirm'
    _description = 'Wizard lines confirm'

    wizard_id = fields.Many2one(
        comodel_name='stock.barcodes.dummy.label',
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
        comodel_name='stock.production.lot',
        string='Lot',
        domain='[("product_id", "=", product_id), '
               '("id", "in", lots_with_stock_ids)]',
    )
    qty = fields.Integer(
        string='Quantity',
    )
    dummy_id = fields.Many2one(
        comodel_name='stock.quant.package_dummy',
        string='Dummy',
    )
    dummy_type = fields.Selection(
        string='Dummy type',
        related='dummy_id.type_id.dummy_type',
        readonly=True,
    )
    pallet_barcode = fields.Char(
        string='Pallet barcode',
    )
    lots_with_stock_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        relation='stock_barcode_dummy_confirm2lot_rel',
        column1='dummy_confirm_id',
        column2='lot_id',
        string='Lots with stock',
        compute='_compute_lots_with_stock_ids',
        store=True,
    )

    @api.depends('product_id', 'qty')
    def _compute_lots_with_stock_ids(self):
        for confirm_line in self:
            if confirm_line.product_id.tracking == 'none':
                confirm_line.lots_with_stock_ids = [(6, 0, [])]
                continue
            location_id = confirm_line.wizard_id.picking_id.location_id.id
            lots = self.env['stock.production.lot'].search([
                ('product_id', '=', confirm_line.product_id.id),
            ])
            lots_with_stock_ids = []
            for lot in lots:
                qty_available = confirm_line.product_id.with_context(
                    location=location_id,
                    lot_id=lot.id
                ).qty_available
                if qty_available >= confirm_line.qty:
                    lots_with_stock_ids.append(lot.id)
            confirm_line.lots_with_stock_ids = [(6, 0, lots_with_stock_ids)]

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        self._origin.lot_id = self.lot_id.id
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', self._origin.wizard_id.picking_id.id),
        ])
        logs.write({'active': False})
        if hasattr(self, '_origin'):
            confirm_lines = self._origin.wizard_id.confirm_line_ids
        else:
            confirm_lines = self.wizard_id.confirm_line_ids
        for line in confirm_lines:
            self.env['stock.barcodes.dummy.log'].create({
                'picking_id': self._origin.wizard_id.picking_id.id,
                'barcode': line.barcode,
                'product_id': line.product_id.id,
                'lot_id': line.lot_id and line.lot_id.id or False,
                'qty': line.qty,
                'dummy_id': line.dummy_id.id,
                'pallet_barcode': line.pallet_barcode,
                'active': True,
            })
        return

    def action_remove_line(self):
        wizard_id = self.wizard_id
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', wizard_id.picking_id.id),
        ])
        for rec_1, rec_2 in zip(wizard_id.confirm_line_ids, logs):
            rec_1.pallet_barcode = rec_2.pallet_barcode
        self.unlink()
        logs.write({'active': False})
        for line in wizard_id.confirm_line_ids:
            self.env['stock.barcodes.dummy.log'].create({
                'picking_id': wizard_id.picking_id.id,
                'barcode': line.barcode,
                'product_id': line.product_id.id,
                'lot_id': line.lot_id and line.lot_id.id or False,
                'qty': line.qty,
                'dummy_id': line.dummy_id.id,
                'pallet_barcode': line.pallet_barcode,
                'active': True,
            })
        for line in wizard_id.line_ids:
            confirm_lines = wizard_id.confirm_line_ids.filtered(
                lambda ln: ln.product_id == line.product_id)
            if not confirm_lines:
                moves = wizard_id.picking_id.move_lines.filtered(
                    lambda m: m.product_id == line.product_id)
                qty_res = sum(moves.mapped('product_uom_qty')) - sum(
                    moves.mapped('quantity_done'))
                line.qty = qty_res
                continue
            moves = wizard_id.picking_id.move_lines.filtered(
                lambda m: m.product_id == confirm_lines[0].product_id)
            qty_res = sum(moves.mapped('product_uom_qty')) - sum(
                moves.mapped('quantity_done'))
            line.qty = qty_res - sum(confirm_lines.mapped('qty'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.barcodes.dummy.label',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard_id.id,
            'target': 'new',
            'context': {},
        }
