###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockInventoryBarcodeIsbn(models.Model):
    _name = 'stock.inventory.barcode.isbn'
    _description = 'Stock inventory quick entry ISBN barcode'

    name = fields.Char(
        string='Name',
    )
    _barcode_scanned = fields.Char(
        string='Barcode scanned',
        help='Last barcode scanned',
        store=False,
    )
    barcode = fields.Char(
        string='Barcode',
    )
    message = fields.Char(
        string='Message',
    )
    message_type = fields.Selection(
        selection=[
            ('success', 'Barcode read correctly'),
            ('error', 'Barcode not read correctly'),
        ],
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name='stock.inventory.barcode.isbn.line',
        inverse_name='inventory_id',
        string='Inventory lines',
    )
    non_editable_line_ids = fields.One2many(
        related='line_ids',
        string='Non editable inventory lines',
    )
    state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('close', 'Close'),
        ],
        default='open',
        required=True,
    )
    container_id = fields.Many2one(
        comodel_name='stock.inventory.barcode.isbn.container',
        string='Container',
    )
    container_live = fields.Boolean(
        string='Container live',
        related='container_id.is_live_container',
    )

    def action_container_close(self):
        self.ensure_one()
        self.container_id.is_live_container = False

    def action_container_print(self):
        self.ensure_one()
        return self.container_id.action_print_inventory_container_label()

    def action_container_in(self):
        self.ensure_one()
        container = self.container_id.search([
            ('is_live_container', '=', True),
        ])
        if not container:
            container = container.create({
                'is_live_container': True,
            })
        self.container_id = container.id

    def action_container_out(self):
        self.ensure_one()
        self.container_id = False

    def action_close_inventory(self):
        self.ensure_one()
        self.state = 'close'

    def action_open_inventory(self):
        self.ensure_one()
        self.state = 'open'

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    _('The name "%s" already exists!') % record.name)

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'stock.inventory.barcode.isbn') or '/'
        return super().create(vals)

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
        self.read_barcode(barcode)
        return

    @api.onchange('_barcode_scanned')
    def _on_barcode_scanned(self):
        barcode = self._barcode_scanned
        if barcode:
            self._barcode_scanned = ''
            return self.on_barcode_scanned(barcode)

    def read_barcode(self, barcode):
        line = self.line_ids.filtered(lambda x: x.barcode == barcode)
        if line:
            line.product_qty += 1
            self._set_message_info('success', _('Read correctly'))
            return
        product = self.env['product.product'].search_or_create_product_by_isbn(
            barcode)
        self.env['stock.inventory.barcode.isbn.line'].create({
            'inventory_id': self.id,
            'barcode': barcode,
            'product_id': product.id if product else False,
            'product_qty': 1,
        })
        if product:
            self._set_message_info('success', _('Read correctly'))
        else:
            self._set_message_info('error', _('ISBN not found'))

    def _set_message_info(self, message_type, message):
        self.message_type = message_type
        if self.barcode:
            self.message = _('ISBN: %s (%s)') % (self.barcode, message)
        else:
            self.message = '%s' % message

    def action_print_inventory_isbn_label(self):
        report = self.env.ref(
            'stock_inventory_barcode_isbn.action_report_inventory_isbn')
        return report.report_action(self)


class StockInventoryBarcodeIsbnLine(models.Model):
    _name = 'stock.inventory.barcode.isbn.line'
    _description = 'Stock inventory barcode ISBN line'

    inventory_id = fields.Many2one(
        comodel_name='stock.inventory.barcode.isbn',
        string='Inventory',
        ondelete='cascade',
    )
    barcode = fields.Text(
        string='ISBN',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain="[('type', '!=', 'service')]",
    )
    product_qty = fields.Integer(
        string='Quantity',
        default=1,
    )
    container_id = fields.Many2one(
        related='inventory_id.container_id',
        string='Container',
        store=True,
    )

    def update_product_by_isbn(self):
        if self.product_id:
            return self.product_id.update_product_by_isbn(self.barcode)
        product = self.product_id.search_or_create_product_by_isbn(
            self.barcode)
        if product:
            self.product_id = product.id
