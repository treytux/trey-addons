###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends(
        'product_id', 'product_id.product_tmpl_id.dto_group_id', 'product_uom',
        'product_uom_qty', 'order_id.date_order', 'order_id.pricelist_id',
        'order_id.partner_id.dto_group_id', 'order_partner_id',
        'pricelist_item_id', 'company_id', 'display_type')
    def _compute_discount(self):
        super()._compute_discount()
        for line in self:
            line.discount = 0.0
            if not line.product_id or line.display_type:
                continue
            if line._pricelist_rule_excludes_group_discount():
                continue
            discount_group = line._get_matching_discount_group()
            if discount_group:
                line.discount = discount_group.discount

    def _pricelist_rule_excludes_group_discount(self):
        self.ensure_one()
        pricelist = self.order_id.pricelist_id
        if not pricelist:
            return False
        order_date = self.order_id.date_order or fields.Datetime.now()
        qty = self.product_uom_qty or 0.0
        _, rule_id = pricelist._get_product_price_rule(
            self.product_id, qty, uom=self.product_uom, date=order_date
        )
        if not rule_id:
            return False
        rule = self.env['product.pricelist.item'].browse(rule_id)
        return not rule.apply_discount_group

    def _get_matching_discount_group(self):
        self.ensure_one()
        partner = self.order_id.partner_id
        if not partner:
            return self.env['discount.group']
        partner_group = partner.dto_group_id
        product_group = self.product_id.dto_group_id
        if not partner_group or not product_group:
            return self.env['discount.group']
        company = (
            self.company_id
            or self.order_id.company_id
            or self.env.company
        )
        order_date = self.order_id.date_order or fields.Datetime.now()
        domain = [
            ('company_id', '=', company.id),
            ('product_id', '=', product_group.id),
            ('partner_id', '=', partner_group.id),
            ('date_start', '<=', order_date),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', order_date),
        ]
        return self.env['discount.group'].search(domain, limit=1)
