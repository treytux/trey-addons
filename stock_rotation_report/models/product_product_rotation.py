# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import date
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp

import logging
_log = logging.getLogger(__name__)


class ProductProductStockRotation(models.Model):
    _name = 'product.product.stock.rotation'
    _description = 'Product stock rotation'
    _rec_name = 'product_id'

    date = fields.Date(
        string='Date',
        required=True,
        select=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        change_default=True,
        required=True,
        select=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        select=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        select=True,
    )
    product_mrp = fields.Boolean(
        string='Product MRP',
    )
    category_id = fields.Many2one(
        related='product_id.product_tmpl_id.categ_id',
        store=True,
    )
    year = fields.Integer(
        string='Year',
        select=True,
    )
    month = fields.Integer(
        string='Month',
        select=True,
    )
    qty_stock_init = fields.Float(
        string='Stock init',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    qty_stock_end = fields.Float(
        string='Stock end',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    qty_move = fields.Float(
        string='Move Quantity',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    qty_purchase = fields.Float(
        string='Purchase',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    qty_sale = fields.Float(
        string='Sales',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    qty_inventory = fields.Float(
        string='Inventories',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    qty_production = fields.Float(
        string='Manufacturing',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    standard_price = fields.Float(
        string='Standard price',
        digits=dp.get_precision('Account'),
    )
    rate_qty = fields.Float(
        string='Rate quantity',
    )
    rate_price = fields.Float(
        string='Rate price',
    )
    rate_percentage = fields.Float(
        string='Rate %',
    )
    rate_qty_year = fields.Float(
        string='Rate quantity year',
    )
    rate_price_year = fields.Float(
        string='Rate price year',
    )
    rate_percentage_year = fields.Float(
        string='Rate % year',
    )

    @api.model
    def stock_move_search(self, company, date_from, date_to=None, product=None,
                          origin_usage=None, dest_usage=None, warehouse=None):
        domain = [
            ('company_id', '=', company.id),
            ('date', '>=', fields.Date.to_string(date_from)),
            ('date', '<=', fields.Date.to_string(date_to)),
            ('state', '!=', 'cancel'),
        ]
        if (origin_usage or dest_usage) == 'inventory':
            domain.append(('inventory_id', '!=', False))
        elif (origin_usage or dest_usage) == 'production':
            domain.append(('production_id', '!=', False))
        else:
            domain.append(('warehouse_id', '=', warehouse.id))
        if product:
            domain.append(('product_id', '=', product.id))
        if origin_usage:
            domain.append(('location_id.usage', '=', origin_usage))
        if dest_usage:
            domain.append(('location_dest_id.usage', '=', dest_usage))
        return self.env['stock.move'].search(domain)

    @api.model
    def calculate_rotation(self, price=None, qty_sale=None, stock_init=None,
                           stock_end=None, is_mrp=False, qty_production=None):
        result = {}
        if qty_sale == 0.00 or (stock_init + stock_end) == 0.00:
            result['rate_price'] = 0.00
            result['rate_qty'] = 0.00
            result['percentage'] = 0.00
            return result
        if not is_mrp:
            qty_sale += qty_production
        average_inventory = (stock_init + stock_end) / 2
        result['rate_qty'] = qty_sale / average_inventory
        result['percentage'] = round(((qty_sale / average_inventory) * 100), 0)
        if price != 0.00:
            result['rate_price'] = (
                (qty_sale * price) / (average_inventory * price))
        else:
            result['rate_price'] = 0.00
        return result

    @api.multi
    def compute_quantities_by_date(self, date_from=None, date_to=None,
                                   company=None):
        if not company:
            return False
        product_ids = self.env['product.product'].search([
            ('type', 'not in', ('consu', 'service'))])
        warehouse_ids = self.env['stock.warehouse'].search([(
            'company_id', '=', company.id)])
        for warehouse in warehouse_ids:
            for product in product_ids:
                is_stats = bool(self.search([
                    ('warehouse_id', '=', warehouse.id),
                    ('product_id', '=', product.id),
                    ('company_id', '=', company.id),
                    ('year', '=', date_from.year),
                    ('month', '=', date_from.month)], limit=1))
                if is_stats:
                    continue
                product_mrp = False
                if product.product_tmpl_id.bom_count != 0:
                    product_mrp = True
                sales_out_moves = self.stock_move_search(
                    company=company, date_from=date_from, date_to=date_to,
                    product=product, dest_usage='customer',
                    warehouse=warehouse)
                sales_in_moves = self.stock_move_search(
                    company=company, date_from=date_from,
                    date_to=date_to, product=product, origin_usage='customer',
                    warehouse=warehouse)
                purchase_out_moves = self.stock_move_search(
                    company=company, date_from=date_from,
                    date_to=date_to, product=product, dest_usage='supplier',
                    warehouse=warehouse)
                purchase_in_moves = self.stock_move_search(
                    company=company, date_from=date_from,
                    date_to=date_to, product=product, origin_usage='supplier',
                    warehouse=warehouse)
                if product_mrp is True:
                    production_out_moves = self.stock_move_search(
                        company=company, date_from=date_from,
                        date_to=date_to, product=product,
                        origin_usage='production', dest_usage='internal',
                        warehouse=warehouse)
                    production_in_moves = 0
                else:
                    production_out_moves = self.stock_move_search(
                        company=company, date_from=date_from,
                        date_to=date_to, product=product,
                        dest_usage='internal', origin_usage='production',
                        warehouse=warehouse)
                    production_in_moves = self.stock_move_search(
                        company=company, date_from=date_from,
                        date_to=date_to, product=product,
                        origin_usage='internal', dest_usage='production',
                        warehouse=warehouse)
                inventory_out_moves = self.stock_move_search(
                    company=company, date_from=date_from,
                    date_to=date_to, product=product,
                    origin_usage='inventory', dest_usage='internal',
                    warehouse=warehouse)
                inventory_in_moves = self.stock_move_search(
                    company=company, date_from=date_from,
                    date_to=date_to, product=product,
                    dest_usage='inventory', origin_usage='internal',
                    warehouse=warehouse)
                sales_moves = (round((
                    sum(sales_out_moves.mapped('product_uom_qty')) -
                    sum(sales_in_moves.mapped('product_uom_qty'))), 0))
                purchase_moves = (round((
                    sum(purchase_in_moves.mapped('product_uom_qty')) -
                    sum(purchase_out_moves.mapped('product_uom_qty'))), 0))
                inventory_moves = (round((
                    sum(inventory_out_moves.mapped('product_uom_qty')) -
                    sum(inventory_in_moves.mapped('product_uom_qty'))), 0))
                if not product_mrp:
                    production_moves = (round((
                        sum(production_out_moves.mapped('product_uom_qty')) -
                        sum(production_in_moves.mapped(
                            'product_uom_qty'))), 0))
                else:
                    production_moves = sum(production_out_moves.mapped(
                        'product_uom_qty'))
                domain = [('warehouse_id', '=', warehouse.id),
                          ('product_id', '=', product.id),
                          ('company_id', '=', company.id)]
                if date_from.month == 1:
                    domain.append(('year', '=', date_from.year - 1))
                    domain.append(('month', '=', 12))
                else:
                    domain.append(('year', '=', date_from.year))
                    domain.append(('month', '=', date_from.month - 1))
                stats_ids = self.search(domain, limit=1)
                if not stats_ids.qty_stock_end:
                    qty_stock_init = 0 + inventory_moves
                else:
                    qty_stock_init = stats_ids.qty_stock_end
                qty_stock_end = (qty_stock_init - sales_moves +
                                 purchase_moves + inventory_moves +
                                 production_moves)
                qty_move = (qty_stock_end - qty_stock_init)
                stats = self.calculate_rotation(
                    price=product.standard_price,
                    qty_sale=sales_moves, stock_init=qty_stock_init,
                    stock_end=qty_stock_end, is_mrp=product_mrp,
                    qty_production=production_moves)
                self.create({
                    'date': date_to,
                    'company_id': company.id,
                    'warehouse_id': warehouse.id,
                    'product_id': product.id,
                    'product_mrp': product_mrp,
                    'year': date_from.year,
                    'month': date_from.month,
                    'qty_move': qty_move,
                    'qty_inventory': inventory_moves,
                    'qty_stock_init': qty_stock_init,
                    'qty_stock_end': qty_stock_end,
                    'qty_purchase': purchase_moves,
                    'qty_sale': sales_moves,
                    'qty_production': production_moves,
                    'standard_price': product.standard_price,
                    'rate_qty': stats['rate_qty'],
                    'rate_price': stats['rate_price'],
                    'rate_percentage': stats['percentage'],
                })
        self.env.cr.commit()

    @api.multi
    def compute_stock_rotation_month(self, init_date=None, company=None):
        _log.info('Start month compute stats process')
        today = fields.Date.from_string(fields.Date.today())
        date_difference = relativedelta(today, init_date)
        number_moths = date_difference.months + (date_difference.years * 12)
        first_day_of_month = date(init_date.year, init_date.month, 1)
        last_day_of_month = (first_day_of_month + relativedelta(
            days=-1, months=1))
        while number_moths > -1:
            _log.info('Generate stats from: %s to: %s' % (
                first_day_of_month, last_day_of_month))
            self.compute_quantities_by_date(
                date_from=first_day_of_month, date_to=last_day_of_month,
                company=company)
            number_moths -= 1
            first_day_of_month += relativedelta(months=+1)
            last_day_of_month = first_day_of_month + relativedelta(
                days=-1, months=+1)
            _log.info('Finish')
        _log.info('End compute stats process')

    @api.multi
    def compute_stock_rotation_year(self):
        _log.info('Start year compute stats process')
        sql_query = '''
            SELECT
                ppsr.company_id,
                ppsr.warehouse_id,
                ppsr.product_id,
                ppsr.year,
                SUM(ppsr.qty_sale) AS qty_sale,
                SUM(ppsr.qty_production) AS qty_production
            FROM
                product_product_stock_rotation ppsr
            GROUP BY
                ppsr.company_id,
                ppsr .warehouse_id,
                ppsr.product_id,
                ppsr.year
            ORDER BY
                year ASC
        '''
        self.env.cr.execute(sql_query)
        products = self.env.cr.fetchall()
        for product in products:
            stats = self.search([
                ('company_id', '=', product[0]),
                ('warehouse_id', '=', product[1]),
                ('product_id', '=', product[2]), ('year', '=', product[3]),
            ])
            year_month_init = stats.filtered(lambda s: s.month == 1)
            year_month_end = stats.filtered(lambda s: s.month == 12)
            if not year_month_end or not year_month_init:
                continue
            price = ((year_month_init.standard_price +
                      year_month_end.standard_price)) / 2
            year_rates = self.calculate_rotation(
                price=price,
                qty_sale=product[4],
                qty_production=product[5],
                stock_init=year_month_init.qty_stock_init,
                stock_end=year_month_end.qty_stock_end,
                is_mrp=year_month_end.product_mrp,
            )
            for stat in stats:
                stat.write({
                    'rate_price_year': year_rates['rate_price'],
                    'rate_qty_year': year_rates['rate_qty'],
                    'rate_percentage_year': year_rates['percentage'],
                })
        _log.info('End compute stats process')

    @api.multi
    def cron_run_compute_stock_rotation_month(self):
        company_ids = self.env['res.company'].search([
            ('is_stock_rotation', '=', True)])
        today = fields.Date.from_string(fields.Date.today())
        for company in company_ids:
            if company.rotation_init_date:
                init_date = fields.Date.from_string(company.rotation_init_date)
                self.compute_stock_rotation_month(
                    init_date=init_date, company=company)
            else:
                self.compute_stock_rotation_month(
                    init_date=today, company=company)

    @api.multi
    def cron_run_compute_stock_rotation_year(self):
        self.compute_stock_rotation_year()
