###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class StockPackageDummyRead(models.TransientModel):
    _name = 'stock.package_dummy.read'
    _description = 'Create stock quant package from dummy'

    action = fields.Char(
        string='Action',
        default='stock',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
        domain='[("usage", "=", "internal")]',
    )
    barcodes = fields.Text(
        string='Barcodes',
        default='',
        required=True,
    )
    step = fields.Integer(
        string='Step',
    )
    line_ids = fields.One2many(
        comodel_name='stock.package_dummy.read.log',
        inverse_name='wizard_id',
        string='Log',
    )
    has_error = fields.Boolean(
        string='Has errors',
        compute='_compute_has_error',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )

    @api.depends('line_ids')
    def _compute_has_error(self):
        for wizard in self:
            wizard.has_error = bool(
                wizard.line_ids.filtered(lambda ln: ln.type == 'error'))

    def log(self, name, barcode, type='error'):
        self.ensure_one()
        self.line_ids.create({
            'wizard_id': self.id,
            'type': type,
            'name': name,
            'barcode': barcode,
        })

    def barcodes_to_list(self):
        self.ensure_one()
        txt = self.barcodes
        txt = txt.split('\n')
        txt = [t.strip() for t in txt]
        return [t for t in txt if t]

    def _simulate_from_stock(self, dummies):
        quant_obj = self.env['stock.quant']
        package_obj = self.env['stock.quant.package']
        for barcode, dummy in dummies.items():
            if not dummy.product_id:
                self.log(_('Dummy label dont know the product'), barcode)
                continue
            package = package_obj.search([('name', '=', barcode)], limit=1)
            if package and package.quant_ids:
                self.log(_('Dummy label in use'), barcode)
                continue
            available_qty = quant_obj._get_available_quantity(
                dummy.product_id, self.location_id)
            need_qty = dummy.packaging_id and dummy.packaging_id.qty or 1
            if available_qty < need_qty:
                self.log(
                    _('Not available quantity in %s') % self.location_id.name,
                    barcode)

    def _simulate_from_stock_picking(self, dummies):
        self._simulate_from_stock(dummies)
        totals = {}
        for barcode, dummy in dummies.items():
            lines = self.picking_id.move_line_ids.filtered(
                lambda ln: ln.product_id == dummy.product_id)
            if not lines:
                self.log(
                    _('The product is not required for this picking'), barcode)
                continue
            qty_total = sum(lines.mapped('product_uom_qty'))
            totals.setdefault(dummy.product_id, qty_total)
            totals[dummy.product_id] -= (
                dummy.packaging_id and dummy.packaging_id.qty or 1)
            if totals[dummy.product_id] < 0:
                self.log(
                    _('More quantity realised than ordered, product %s') % (
                        dummy.product_id.name),
                    barcode,
                    type='warning')

    def simulate(self):
        self.ensure_one()
        barcodes = self.barcodes_to_list()
        dummy_obj = self.env['stock.quant.package_dummy']
        dummies = {}
        duplicates = []
        for barcode in barcodes:
            if barcode not in duplicates and barcodes.count(barcode) > 1:
                duplicates.append(barcode)
                self.log(_('Duplicate dummy label'), barcode, 'warning')
                continue
            dummy = dummy_obj.search_from_barcode(barcode)
            if not dummy:
                self.log(_('Dummy label not exist'), barcode)
                continue
            dummies[barcode] = dummy
        fnc = getattr(self, '_simulate_from_%s' % self.action)
        fnc(dummies)

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

    def action_back(self):
        self.step = 0
        return self._reopen_view()

    def action_simulate(self):
        self.line_ids.unlink()
        self.simulate()
        self.step = 1
        return self._reopen_view()

    def action_run(self):
        self.ensure_one()
        if self.has_error:
            raise exceptions.UserError(_('Problems must be solved first'))
        action = '_run_create_packages_from_%s' % self.action
        fnc = getattr(self, action)
        return fnc()

    def _run_create_packages_from_stock(self):
        self.ensure_one()
        barcodes = self.barcodes_to_list()
        dummy_obj = self.env['stock.quant.package_dummy']
        warehouse = self.location_id.get_warehouse()
        self.picking_id = self.env['stock.picking'].create({
            'move_type': 'direct',
            'partner_id': self.env.user.company_id.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
            'picking_type_id': warehouse.int_type_id.id,
        })
        move_obj = self.env['stock.move']
        dummies = {}
        for barcode in barcodes:
            dummy = dummy_obj.search_from_barcode(barcode)
            if not dummy:
                continue
            if not dummy.product_id:
                continue
            dummies[barcode] = dummy
            pack = dummy.create_pack(barcode)
            move_obj.create({
                'name': dummy.product_id.name,
                'origin': barcode,
                'product_id': dummy.product_id.id,
                'product_uom_qty': (
                    dummy.packaging_id and dummy.packaging_id.qty or 1),
                'product_uom': dummy.product_id.uom_id.id,
                'picking_id': self.picking_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_id.id,
                'product_packaging': dummy.packaging_id.id,
            })
        if not self.picking_id.move_lines:
            raise exceptions.UserError(
                _('Package without products, revise barcodes'))
        self.picking_id.action_confirm()
        if self.picking_id.state != 'confirmed':
            raise exceptions.UserError(
                _('Impossible to create confirmed picking. '
                  'Please check products availability!'))
        self.picking_id.action_assign()
        if self.picking_id.state != 'assigned':
            raise exceptions.UserError(
                _('Impossible to create confirmed picking. '
                  'Please check products availability!'))
        for line in self.picking_id.move_line_ids:
            key = [k for k in dummies.keys() if k in line.move_id.origin]
            dummy = dummies[key[0]]
            line.write({
                'result_package_id': pack.id,
                'qty_done': line.product_uom_qty,
                'lot_id': dummy.lot_id.id,
            })
        self.picking_id.with_context(
            skip_update_line_ids=True).action_confirm()
        self.picking_id.action_done()

    def assing_dummy_in_moves(self, moves, barcode):
        dummy = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcode)
        if not dummy:
            return False, False
        qty = (dummy.packaging_id and dummy.packaging_id.qty or 1)
        pack = dummy.create_pack(barcode)
        move_lines = moves.mapped('move_line_ids').filtered(
            lambda ml: (
                ml.product_id == dummy.product_id
                and not ml.result_package_id
                and ml.product_uom_qty - ml.qty_done >= qty
            )
        )
        if not move_lines:
            return dummy, False
        move_line = move_lines.create({
            'move_id': move_lines[0].move_id.id,
            'product_id': move_lines[0].product_id.id,
            'location_id': move_lines[0].location_id.id,
            'location_dest_id': move_lines[0].location_dest_id.id,
            'product_uom_id': move_lines[0].move_id.product_uom.id,
            'qty_done': qty,
            'lot_id': dummy.lot_id.id,
            'result_package_id': pack.id,
        })
        return dummy, move_line

    def _run_create_packages_from_stock_picking(self):
        self.ensure_one()
        if not self.picking_id:
            raise exceptions.UserError(_('Launch this wizard from picking'))
        barcodes = self.barcodes_to_list()
        moves = self.picking_id.move_lines
        for barcode in barcodes:
            dummy, move_line = self.assing_dummy_in_moves(moves, barcode)
            if not dummy:
                raise exceptions.ValidationError(
                    _('Barcode %s not exist') % barcode)
            if not move_line:
                need_product = moves.filtered(
                    lambda m: dummy.product_id == m.product_id)
                if need_product:
                    raise exceptions.ValidationError(_(
                        'Barcode %s not generate move line.\n'
                        'You introduce more quantity than necesary of product '
                        '"%s"') % (barcode, dummy.product_id.name))
                raise exceptions.ValidationError(_(
                    'Barcode %s not generate move line.\n'
                    'Product "%s" is not necesary for this picking.'))


class StockPackageDummyReadLog(models.TransientModel):
    _name = 'stock.package_dummy.read.log'
    _description = 'Log when create stock quant package from dummy'

    wizard_id = fields.Many2one(
        comodel_name='stock.package_dummy.read',
        string='Wizard',
    )
    type = fields.Selection(
        selection=[
            ('error', 'Error'),
            ('warning', 'Warning'),
        ],
        string='Type',
        default='error',
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    barcode = fields.Char(
        string='Barcode',
        required=True,
    )
