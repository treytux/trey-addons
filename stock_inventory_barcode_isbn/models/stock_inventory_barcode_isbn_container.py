###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockInventoryBarcodeIsbnContainer(models.Model):
    _name = 'stock.inventory.barcode.isbn.container'
    _description = 'Stock inventory ISBN container'

    name = fields.Char(
        string='Name',
    )
    is_live_container = fields.Boolean(
        string='Is live container',
    )
    line_ids = fields.One2many(
        comodel_name='stock.inventory.barcode.isbn',
        inverse_name='container_id',
        string='Isbn lines',
    )

    def action_close_container(self):
        self.ensure_one()
        self.is_live_container = False

    def action_open_container(self):
        self.ensure_one()
        containers = self.search([
            ('is_live_container', '=', True),
        ])
        containers.write({
            'is_live_container': False,
        })
        self.is_live_container = True

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            if not record.is_live_container:
                continue
            live_containers = self.search([
                ('is_live_container', '=', True),
                ('id', '!=', record.id),
            ], limit=1)
            if live_containers:
                raise ValidationError(_('Only one container can be active!'))

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'stock.inventory.barcode.isbn.container') or '/'
        return super().create(vals)

    def action_print_inventory_container_label(self):
        report = self.env.ref(
            'stock_inventory_barcode_isbn.action_report_isbn_container')
        return report.report_action(self)
