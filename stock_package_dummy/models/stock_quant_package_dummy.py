###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models

try:
    from checkdigit import gs1
except ImportError:
    gs1 = None


class StockQuantPackageDummy(models.Model):
    _name = 'stock.quant.package_dummy'
    _description = 'Stock quant package dummy'
    _rec_name = 'barcode_prefix'

    barcode_prefix = fields.Char(
        string='Barcode',
    )
    barcode_start_number = fields.Integer(
        string='Barcode start number',
        default=0,
    )
    qty = fields.Integer(
        string='Quantity of labels',
        required=True,
    )
    auto_generate_barcodes = fields.Boolean(
        string='Auto generate barcodes',
        default=True,
    )
    barcodes = fields.Text(
        string='Barcodes',
        compute='_compute_barcodes',
        store=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
        string='Product',
    )
    packaging_id = fields.Many2one(
        comodel_name='product.packaging',
        string='Packaging',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial',
    )

    def _barcode_prefix_get(self):
        prefix = self.env['ir.config_parameter'].get_param(
            'stock_package_dummy.prefix', default='0' * 8)
        return '%s%s' % (prefix, str(self.id or 0).zfill(5))

    def get_barcodes(self):
        self.ensure_one()
        return self._get_barcodes(
            self.barcode_prefix, self.qty, self.barcode_start_number)

    def _get_barcode_sscc(self, prefix, number):
        fill = 17 - len(prefix)
        code = '%s%s' % (prefix, str(number).zfill(fill))
        code = '%s%s' % (code, gs1.calculate(code))
        if len(code) > 18:
            raise exceptions.UserError(_(
                'Barcode %s generate has more than 18 digits, please reduce '
                'the prefix system param or print less labels') % code)
        return code

    @api.model
    def _get_barcodes(self, barcode_prefix, qty, start=0):
        return [
            self._get_barcode_sscc(barcode_prefix or '0', n)
            for n in range(start, start + qty)]

    @api.depends('barcode_prefix')
    def _compute_barcodes(self):
        for dummy in self:
            if not dummy.auto_generate_barcodes:
                continue
            dummy.barcodes = '\n'.join(dummy.get_barcodes())

    @api.constrains('lot_id', 'packaging_id')
    def _check_lot_and_packaging(self):
        for dummy in self:
            product = dummy.product_id
            if dummy.lot_id and product != dummy.lot_id.product_id:
                raise exceptions.ValidationError(_(
                    'Product for dummy package must be the same for the lot'))
            if dummy.packaging_id and product != dummy.packaging_id.product_id:
                raise exceptions.ValidationError(_(
                    'Product for dummy package must be the same for the '
                    'packaging'))

    @api.constrains('barcode_prefix')
    def _check_duplicated_barcode_prefix(self):
        for dummy in self:
            records = dummy.search([
                ('id', '!=', dummy.id),
                ('auto_generate_barcodes', '=', True),
                ('barcode_prefix', '=like', '%s%%' % dummy.barcode_prefix),
            ])
            if not records:
                continue
            raise exceptions.ValidationError(_(
                'There can only be one barcode prefix %s for the dummy '
                'label.\nTry to print the labels again.') % (
                    dummy.barcode_prefix))

    @api.model
    def create(self, vals):
        dummy = super().create(vals)
        if 'barcode_prefix' not in vals:
            dummy.barcode_prefix = dummy._barcode_prefix_get()
        return dummy

    @api.model
    def search_from_barcode(self, barcode):
        prefix = self._barcode_prefix_get()
        prefix = barcode[:len(prefix)]
        dummies = self.search([
            ('barcode_prefix', '=', prefix),
            ('auto_generate_barcodes', '=', True),
        ])
        if dummies:
            return dummies.filtered(
                lambda d: barcode in d.barcodes.split('\n'))
        dummies = self.search([
            ('barcodes', '=', barcode),
            ('auto_generate_barcodes', '=', False),
        ], limit=1)
        return dummies

    def create_pack(self, barcode):
        self.ensure_one()
        pack_obj = self.env['stock.quant.package']
        pack = pack_obj.search([('name', '=', barcode)], limit=1)
        if not pack:
            pack = pack.create({'name': barcode, 'dummy_id': self.id})
        return pack[0]
