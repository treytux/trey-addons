###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class ProductCustomerinfoCopy(models.TransientModel):
    _name = 'product.customerinfo.copy'
    _description = 'Wizard to copy product customer info.'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        domain=[('customer', '=', True)],
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='product.customerinfo.copy.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'line_ids' not in res:
            res['line_ids'] = []
        product_customerinfos = self.env['product.customerinfo'].browse(
            self.env.context.get('active_ids', []))
        for product_customerinfo in product_customerinfos:
            line = {
                'wizard_id': self.id,
                'partner_id': product_customerinfo.name.id,
                'product_id': product_customerinfo.product_id.id,
                'product_tmpl_id': product_customerinfo.product_tmpl_id.id,
                'sequence': product_customerinfo.sequence,
                'product_name': product_customerinfo.product_name,
                'product_code': product_customerinfo.product_code,
                'min_qty': product_customerinfo.min_qty,
                'price': product_customerinfo.price,
                'delay': product_customerinfo.delay,
                'date_start': product_customerinfo.date_start,
                'date_end': product_customerinfo.date_end,
            }
            res['line_ids'].append((0, 0, line))
        return res

    @api.multi
    def button_accept(self):
        self.ensure_one()
        product_customerinfo_obj = self.env['product.customerinfo']
        for line in self.line_ids:
            product_customer_exists = product_customerinfo_obj.search([
                ('name', '=', self.partner_id.id),
                ('product_tmpl_id', '=', line.product_tmpl_id.id),
                ('price', '=', line.price),
                ('min_qty', '=', line.min_qty),
            ])
            if product_customer_exists:
                continue
            product_customerinfo_obj.create({
                'name': self.partner_id.id,
                'product_id': line.product_id.id,
                'product_tmpl_id': line.product_tmpl_id.id,
                'sequence': line.sequence,
                'product_name': line.product_name,
                'product_code': line.product_code,
                'min_qty': line.min_qty,
                'delay': line.delay,
                'price': line.price,
                'date_start': line.date_start,
                'date_end': line.date_end,
            })
        view = self.env.ref(
            'product_supplierinfo_for_customer_copy.'
            'wizard_product_customerinfo_copy_end')
        return {
            'name': _('Product customer info created'),
            'res_model': 'product.customerinfo.copy',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
        }


class ProductCustomerinfoCopyLine(models.TransientModel):
    _name = 'product.customerinfo.copy.line'
    _description = 'Wizard lines.'

    wizard_id = fields.Many2one(
        comodel_name='product.customerinfo.copy',
        string='Wizard',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        domain=[('customer', '=', True)],
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    product_name = fields.Char(
        string='Product name',
    )
    product_code = fields.Char(
        string='Product code',
    )
    min_qty = fields.Float(
        string='Minimun quantity',
        required=True,
    )
    delay = fields.Integer(
        string='Delay',
        required=True,
    )
    price = fields.Float(
        string='Price',
    )
    date_start = fields.Date(
        string='Start date',
        help='Start date for this customer price',
    )
    date_end = fields.Date(
        string='End date',
        help='End date for this customer price',
    )
