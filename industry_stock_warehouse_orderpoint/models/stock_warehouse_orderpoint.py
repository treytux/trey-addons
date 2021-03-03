###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import math

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    product_min_qty_year = fields.Float(
        string='Last Year Min Qty',
        digits=dp.get_precision('Product Unit of Measure'),
        help='Monthly average of the movements of exits and returns of '
             'clients in the previous year',
    )
    product_min_qty_month = fields.Float(
        string='Last Month Min Qty',
        digits=dp.get_precision('Product Unit of Measure'),
        help='The movements of exits and returns of clients in the previous '
             'month',
    )
    product_suggested_qty = fields.Float(
        string='Suggestion',
        compute='compute_product_suggested_qty',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    product_buy_qty = fields.Float(
        string='Buy',
        digits=dp.get_precision('Product Unit of Measure'),
    )

    @api.multi
    @api.depends('product_location_qty_available_not_res',
                 'product_min_qty_year')
    def compute_product_suggested_qty(self):
        for op in self:
            op.product_suggested_qty = (op.product_min_qty_year
                                        - op.virtual_location_qty)

    @api.multi
    def stock_move_search(self, company, date_from, date_to=None, product=None,
                          location_id=None, location_dest_id=None,
                          warehouse=None):
        domain = [
            ('company_id', '=', company.id),
            ('date', '<=', date_to),
            ('state', '!=', 'cancel'),
        ]
        if date_from:
            domain.append(('date', '>=', date_from))
        if product:
            domain.append(('product_id', '=', product.id))
        if location_id:
            if warehouse.deposit_parent_id:
                location_ids = warehouse.deposit_parent_id.child_ids.ids
                location_ids.append(location_id)
                domain.append(('location_id', 'in', tuple(location_ids)))
                domain.append(
                    ('picking_type_id.warehouse_id', '=', warehouse.id))
            else:
                domain.append(('location_id', '=', location_id))
        else:
            domain.append(('location_id.usage', '=', 'customer'))
        if location_dest_id:
            if warehouse.deposit_parent_id:
                location_ids = warehouse.deposit_parent_id.child_ids.ids
                location_ids.append(location_dest_id)
                domain.append(('location_dest_id', 'in', tuple(location_ids)))
                domain.append(
                    ('picking_type_id.warehouse_id', '=', warehouse.id))
            else:
                domain.append(('location_dest_id', '=', location_dest_id))
        else:
            domain.append(('location_dest_id.usage', '=', 'customer'))
        return self.env['stock.move'].search(domain)

    @api.multi
    def compute_product_min_qty_year(self):
        date_from = fields.Date.today() - relativedelta(years=1)
        date_to = fields.Date.today()
        for op in self:
            in_moves = self.stock_move_search(
                company=op.company_id,
                date_from=date_from,
                date_to=date_to,
                product=op.product_id,
                location_dest_id=op.location_id.id,
                warehouse=op.warehouse_id,
            )
            out_moves = self.stock_move_search(
                company=op.company_id,
                date_from=date_from,
                date_to=date_to,
                product=op.product_id,
                location_id=op.location_id.id,
                warehouse=op.warehouse_id,
            )
            op.product_min_qty_year = round((
                sum(out_moves.mapped('product_uom_qty'))
                - sum(in_moves.mapped('product_uom_qty'))) / 12, 0)

    @api.model
    def cron_product_min_qty_year(self):
        ops = self.search([])
        ops.compute_product_min_qty_year()

    @api.multi
    def compute_copy_product_suggested_qty(self):
        for op in self:
            qty = (op.product_suggested_qty if op.product_suggested_qty > 0
                   else 0.00)
            if (op.product_id.seller_ids and op.product_id.seller_ids[
                    0].min_qty and qty > 0):
                qty = (math.ceil(qty / op.product_id.seller_ids[0].min_qty)
                       * op.product_id.seller_ids[0].min_qty)
            op.product_buy_qty = qty

    @api.multi
    def compute_rule_quantities_from_product_min_qty_year(self):
        for op in self:
            op.write({
                'product_min_qty': op.product_min_qty_year,
                'product_max_qty': op.product_min_qty_year * 2,
            })

    @api.multi
    def make_procurement(self):
        errors = []
        for op in self:
            values = op._prepare_procurement_values(op.product_buy_qty)
            try:
                self.env['procurement.group'].with_context(
                    requested_uid=self.env.user).run(
                    op.product_id,
                    op.product_buy_qty,
                    op.product_id.uom_id,
                    op.location_id,
                    op.name,
                    op.name,
                    values,
                )
            except UserError as error:
                errors.append(error.name)
            if errors:
                raise UserError('\n'.join(errors))
