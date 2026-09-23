###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html_escape


class SaleOrderConfirmMessage(models.TransientModel):
    _name = 'sale.order.confirm.message'
    _description = 'Quotation confirmation review wizard'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Quotation',
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='order_id.company_id',
        string='Company',
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        string='Currency',
        readonly=True,
    )
    message = fields.Text(
        related='company_id.sale_confirm_message_body',
        string='Message',
        readonly=True,
    )
    require_check = fields.Boolean(
        related='company_id.sale_confirm_message_require_check',
        string='Review check required',
        readonly=True,
    )
    locked_fields_html = fields.Html(
        string='Data locked after confirmation',
        compute='_compute_locked_fields_html',
        sanitize=False,
    )
    checked = fields.Boolean(
        string='I have checked this information against the document signed '
               'by the customer',
    )
    partner_id = fields.Many2one(
        related='order_id.partner_id',
        string='Customer',
        readonly=True,
    )
    partner_shipping_id = fields.Many2one(
        related='order_id.partner_shipping_id',
        string='Delivery Address',
        readonly=True,
    )
    partner_invoice_id = fields.Many2one(
        related='order_id.partner_invoice_id',
        string='Invoice Address',
        readonly=True,
    )
    payment_term_id = fields.Many2one(
        related='order_id.payment_term_id',
        string='Payment Terms',
        readonly=True,
    )
    payment_mode_id = fields.Many2one(
        related='order_id.payment_mode_id',
        string='Payment Mode',
        readonly=True,
    )
    incoterm = fields.Many2one(
        related='order_id.incoterm',
        string='Incoterm',
        readonly=True,
    )
    amount_untaxed = fields.Monetary(
        related='order_id.amount_untaxed',
        string='Untaxed Amount',
        readonly=True,
    )
    amount_tax = fields.Monetary(
        related='order_id.amount_tax',
        string='Taxes',
        readonly=True,
    )
    amount_total = fields.Monetary(
        related='order_id.amount_total',
        string='Total',
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name='sale.order.confirm.message.line',
        inverse_name='wizard_id',
        string='Lines',
        readonly=True,
    )

    @api.depends('order_id')
    def _compute_locked_fields_html(self):
        items = [
            _('Customer'),
            _('Delivery Address'),
            _('Invoice Address'),
            _('Payment Terms'),
            _('Payment Mode'),
            _('Incoterm'),
            _('Line data: product, quantity, unit price, taxes, discount and '
              'subtotal'),
            _('Order totals: untaxed amount, taxes and total'),
        ]
        markup = '<ul class="mb-0">%s</ul>' % ''.join(
            '<li>%s</li>' % html_escape(item) for item in items)
        for wizard in self:
            wizard.locked_fields_html = markup

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order = self.env['sale.order'].browse(
            res.get('order_id') or self.env.context.get('default_order_id'))
        if not order:
            return res
        res['order_id'] = order.id
        lines = []
        for line in order.order_line.filtered(lambda ln: not ln.display_type):
            lines.append((0, 0, {
                'order_line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'tax_id': [(6, 0, line.tax_id.ids)],
                'discount': line.discount,
                'price_subtotal': line.price_subtotal,
            }))
        res['line_ids'] = lines
        return res

    @api.multi
    def action_confirm_order(self):
        self.ensure_one()
        if self.require_check and not self.checked:
            raise UserError(_(
                'Please confirm that you have checked the information against '
                'the document signed by the customer before confirming the '
                'quotation.'))
        return self.order_id.with_context(
            bypass_sale_confirm_message=True).action_confirm()


class SaleOrderConfirmMessageLine(models.TransientModel):
    _name = 'sale.order.confirm.message.line'
    _description = 'Quotation confirmation review wizard line'

    wizard_id = fields.Many2one(
        comodel_name='sale.order.confirm.message',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        related='wizard_id.currency_id',
        string='Currency',
        readonly=True,
    )
    order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    name = fields.Text(
        string='Description',
        readonly=True,
    )
    product_uom_qty = fields.Float(
        string='Quantity',
        readonly=True,
    )
    price_unit = fields.Float(
        string='Unit Price',
        readonly=True,
    )
    tax_id = fields.Many2many(
        comodel_name='account.tax',
        string='Taxes',
        readonly=True,
    )
    discount = fields.Float(
        string='Disc.(%)',
        readonly=True,
    )
    price_subtotal = fields.Monetary(
        string='Subtotal',
        readonly=True,
    )
