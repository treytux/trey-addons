###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPackageDummyPrint(models.TransientModel):
    _name = 'stock.package_dummy.print'
    _description = 'Print stock package dummy'

    @api.model
    def _get_dummy_types_selection(self):
        dummy_type_obj = self.env['stock.quant_package.dummy.type']
        dummys = dummy_type_obj.search([
            ('company_id', '=', self.env.user.company_id.id),
        ]).mapped('dummy_type')
        dummy_list = dummy_type_obj._fields['dummy_type'].selection
        selection_list = []
        for dummy in dummy_list:
            if dummy[0] in dummys:
                selection_list.append(dummy)
        return selection_list

    qty_to_print = fields.Integer(
        string='Qty labels to print',
        default=1,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
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
    dummy_id = fields.Many2one(
        comodel_name='stock.quant.package_dummy',
        string='Dummy label',
    )
    dummy_type = fields.Selection(
        selection=_get_dummy_types_selection,
        string='Label type',
        required=True,
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
            self.dummy_id.barcode_prefix, self.qty_to_print)

    def _get_domain_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(dummy_label)')])
        return [('id', 'in', reports and reports.ids or [0])]

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Report',
        domain=_get_domain_report,
    )

    def get_dummy_type(self):
        dummy_type = self.env['stock.quant_package.dummy.type'].search([
            ('dummy_type', '=', self.dummy_type),
        ])
        if not dummy_type:
            raise ValidationError(
                _('Error: review the types of dummies created in the system'))
        return dummy_type

    @api.onchange('dummy_type')
    def onchange_dummy_type(self):
        for wizard in self:
            dummy_type = self.env['stock.quant_package.dummy.type'].search([
                ('dummy_type', '=', self.dummy_type),
            ])
            if dummy_type and dummy_type.report_id:
                wizard.report_id = dummy_type.report_id.id

    def print_label(self):
        self.ensure_one()
        if not self.report_id:
            dummy_type = self.get_dummy_type()
            self.report_id = dummy_type.report_id.id
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
            dummy_type = self.get_dummy_type()
            self.dummy_id = self.env['stock.quant.package_dummy'].create({
                'qty': self.qty_to_print,
                'product_id': self.product_id.id,
                'packaging_id': self.packaging_id.id,
                'lot_id': self.lot_id.id,
            })
            self.dummy_id.barcode_prefix = '%s%s' % (
                dummy_type.prefix, str(self.dummy_id.id or 0).zfill(5))
            self.dummy_id.get_barcodes()
        action = self.print_label()
        action.update({'close_on_report_download': True})
        return action
