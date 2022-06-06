###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPackageDummyPrint(models.TransientModel):
    _name = 'stock.package_dummy.print'
    _description = 'Print stock package dummy'

    qty_to_print = fields.Integer(
        string='Qty labels to print',
        default=1,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    packaging_id = fields.Many2one(
        comodel_name='product.packaging',
        string='Packaging',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial',
    )
    dummy_id = fields.Many2one(
        comodel_name='stock.quant.package_dummy',
        string='Dummy label',
    )

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        for wizard in self:
            if not wizard.lot_id:
                continue
            wizard.product_id = wizard.lot_id.product_id.id

    def get_barcodes(self):
        self.ensure_one()
        return self.env['stock.quant.package_dummy']._get_barcodes(
            self.dummy_id._barcode_prefix_get(), self.qty_to_print)

    def _get_default_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(dummy_label)')])
        if not reports.exists():
            return None
        return reports[0]

    def _get_domain_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(dummy_label)')])
        return [('id', 'in', reports and reports.ids or [0])]

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Report',
        domain=_get_domain_report,
        default=_get_default_report,
        required=True,
    )

    def print_label(self):
        self.ensure_one()
        action = self.env.ref(
            self.report_id.xml_id).report_action(self.dummy_id)
        action['context'].update({
            'barcode_prefix': self.dummy_id.barcode_prefix,
            'barcodes': self.dummy_id.get_barcodes(),
            'lot_id': self.lot_id.id,
            'packaging_id': self.packaging_id.id,
            'product_id': self.product_id.id,
            'qty_to_print': self.qty_to_print,
        })
        return action

    def action_print(self):
        if not self.dummy_id:
            self.dummy_id = self.env['stock.quant.package_dummy'].create({
                'qty': self.qty_to_print,
                'product_id': self.product_id.id,
                'packaging_id': self.packaging_id.id,
                'lot_id': self.lot_id.id,
            })
            self.dummy_id.get_barcodes()
        return self.print_label()
