###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customerinfo_id = fields.Many2one(
        comodel_name='product.customerinfo',
        string='Customer Product Reference',
        check_company=True,
    )

    def _get_customerinfo_domain(self):
        self.ensure_one()
        domain = []
        if self.product_id:
            domain = [
                '|',
                ('product_id', '=', self.product_id.id),
                '&',
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('product_id', '=', False),
            ]
        partner = self.order_partner_id or self.order_id.partner_id
        if partner:
            partner_ids = (
                partner + partner.parent_id + partner.commercial_partner_id).ids
            domain = expression.AND([
                domain, [('partner_id', 'in', partner_ids),]])
        return domain

    def _get_effective_customerinfo(self):
        self.ensure_one()
        return self.customerinfo_id or self._get_default_customerinfo()

    def _get_default_customerinfo(self):
        self.ensure_one()
        if not self.product_id or not self.order_partner_id:
            return self.env['product.customerinfo']
        return self.product_id._select_customerinfo(
            partner=self.order_partner_id)

    def _get_customerinfo_partner_ids(self, partner=False):
        self.ensure_one()
        partner = partner or self.order_partner_id or self.order_id.partner_id
        if not partner:
            return []
        return (partner + partner.parent_id + partner.commercial_partner_id).ids

    def _customerinfo_matches_partner(self, partner=False):
        self.ensure_one()
        if not self.customerinfo_id:
            return True
        partner_ids = self._get_customerinfo_partner_ids(partner=partner)
        if not partner_ids:
            return True
        return self.customerinfo_id.partner_id.id in partner_ids

    def _apply_customerinfo_defaults(self):
        for line in self:
            line.customerinfo_id = line._get_default_customerinfo()
            line._apply_customerinfo_values()

    def _apply_customerinfo_name(self):
        for line in self:
            customerinfo = line._get_effective_customerinfo()
            if not customerinfo:
                continue
            if customerinfo.product_code:
                display_name = customerinfo.product_name or line.name or ''
                line.name = '[%s] %s' % (
                    customerinfo.product_code, display_name)
            elif customerinfo.product_name:
                line.name = customerinfo.product_name

    def _apply_customerinfo_values(self):
        for line in self:
            customerinfo = line._get_effective_customerinfo()
            if not customerinfo:
                continue
            if customerinfo.min_qty:
                line.product_uom_qty = customerinfo.min_qty
            if customerinfo.price or customerinfo.price == 0.0:
                line.price_unit = customerinfo.price
            line._apply_customerinfo_name()

    @api.onchange('product_id', 'order_partner_id')
    def _onchange_customerinfo_id(self):
        domain = {'customerinfo_id': []}
        if self:
            domain['customerinfo_id'] = self._get_customerinfo_domain()
        self._apply_customerinfo_defaults()
        return {'domain': domain}

    @api.onchange('customerinfo_id')
    def _onchange_customerinfo_selection(self):
        self._apply_customerinfo_values()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line, vals in zip(lines, vals_list):
            if vals.get('customerinfo_id') or not line.product_id:
                continue
            customerinfo = line._get_default_customerinfo()
            if customerinfo:
                line.customerinfo_id = customerinfo
                line._apply_customerinfo_values()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if (
            {'product_id', 'order_id', 'order_partner_id'} & set(vals)
                and 'customerinfo_id' not in vals):
            for line in self:
                if not line.product_id:
                    continue
                customerinfo = line._get_default_customerinfo()
                if customerinfo:
                    line.customerinfo_id = customerinfo
                    line._apply_customerinfo_values()
        return res

    @api.constrains('customerinfo_id', 'product_id', 'order_id')
    def _check_customerinfo_partner(self):
        for line in self:
            if not line.product_id or not line.order_id:
                continue
            if line._customerinfo_matches_partner():
                continue
            raise ValidationError(_(
                'Customer Product Reference %(customerinfo)s does not belong '
                'to customer %(partner)s.'
            ) % {
                'customerinfo': line.customerinfo_id.display_name,
                'partner': line.order_id.partner_id.display_name,
            })

    @api.depends(
        'product_id',
        'product_uom',
        'product_uom_qty',
        'customerinfo_id',
        'order_id.partner_id',
        'order_id.pricelist_id'
    )
    def _compute_price_unit(self):
        super()._compute_price_unit()
        for line in self:
            customerinfo = line._get_effective_customerinfo()
            if not customerinfo:
                continue
            price = customerinfo.price
            if (
                customerinfo.product_uom
                and line.product_uom
                and customerinfo.product_uom != line.product_uom
            ):
                price = customerinfo.product_uom._compute_price(
                    price, line.product_uom)
            currency = (
                line.order_id.currency_id
                or (line.order_id.pricelist_id
                    and line.order_id.pricelist_id.currency_id))
            if (currency and customerinfo.currency_id
                    and customerinfo.currency_id != currency):
                company = (line.company_id or line.order_id.company_id
                           or self.env.company)
                price = customerinfo.currency_id._convert(
                    price, currency, company,
                    line.order_id.date_order or fields.Date.context_today(line))
            line.price_unit = price

    @api.depends('product_id', 'customerinfo_id', 'order_id.partner_id')
    def _compute_name(self):
        empty_lines = self.filtered(lambda line: not line.product_id)
        super(SaleOrderLine, empty_lines)._compute_name()
        for line in self:
            if not line.product_id:
                continue
            customerinfo = line._get_effective_customerinfo()
            if not customerinfo:
                continue
            line_to_compute = (
                line.with_context(display_default_code=False)
                if customerinfo.product_code else line)
            super(SaleOrderLine, line_to_compute)._compute_name()
            line._apply_customerinfo_name()
