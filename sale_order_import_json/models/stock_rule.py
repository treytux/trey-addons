###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty,
                                     product_uom, values, po, partner):
        res = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, values, po, partner)
        if not self.env.context.get('supplierinfo'):
            return res
        seller = self.env['product.supplierinfo']
        for line in self.env.context.get('supplierinfo'):
            if (line['line_id'] == values.get('sale_line_id') or (
                    values.get('move_dest_ids', False) and (
                        line['line_id'] in values['move_dest_ids'].mapped(
                            'sale_line_id').ids))) and line['supplierinfo_id']:
                seller = self.env['product.supplierinfo'].browse(
                    line['supplierinfo_id'])
            if (line['line_id'] == values.get('sale_line_id') or (
                    values.get('move_dest_ids', False) and (
                        line['line_id'] in values['move_dest_ids'].mapped(
                            'sale_line_id').ids))) and (
                                not line['supplierinfo_id']):
                return res
        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(
            taxes, product_id, seller.name) if fpos else taxes
        if taxes_id:
            taxes_id = taxes_id.filtered(
                lambda x: x.company_id.id == values['company_id'].id)
        price_unit = 0.0
        if seller:
            tax_obj = self.env['account.tax']
            price_unit = tax_obj._fix_tax_included_price_company(
                seller.price, product_id.supplier_taxes_id, taxes_id,
                values['company_id'])
        if price_unit and seller and po.currency_id and (
                seller.currency_id != po.currency_id):
            price_unit = seller.currency_id._convert(
                price_unit, po.currency_id, po.company_id,
                po.date_order or fields.Date.today())
        product_lang = product_id.with_context({
            'lang': partner.lang,
            'partner_id': partner.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        date_planned = self.env['purchase.order.line']._get_date_planned(
            seller, po=po).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        res.update({
            'name': name,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id.ids)],
        })
        return res
