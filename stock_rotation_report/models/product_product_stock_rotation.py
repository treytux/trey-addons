###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero

_log = logging.getLogger(__name__)


class ProductProductStockRotation(models.Model):
    _name = 'product.product.stock.rotation'
    _description = 'Product stock rotation'
    _rec_name = 'product_id'
    _order = 'date_day asc'

    date_day = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        change_default=True,
        required=True,
        index=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        index=True,
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
        index=True,
    )
    month = fields.Integer(
        string='Month',
        index=True,
    )
    week = fields.Integer(
        string='Week',
        index=True,
    )
    day = fields.Integer(
        string='Day',
        index=True,
    )
    qty_stock_init = fields.Float(
        string='Stock init',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.00,
    )
    qty_stock_end = fields.Float(
        string='Stock end',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.00,
    )
    qty_move = fields.Float(
        string='Move Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.00,
    )
    qty_purchase = fields.Float(
        string='Purchase',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.00,
    )
    qty_sale = fields.Float(
        string='Sales',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    default = 0.00,
    qty_inventory = fields.Float(
        string='Inventories',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    default = 0.00,
    qty_production = fields.Float(
        string='Manufacturing',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    standard_price = fields.Float(
        string='Standard price',
        digits=dp.get_precision('Account'),
        default=0.00,
    )
    rate_qty = fields.Float(
        string='Rate quantity day',
        default=0.00,
    )
    rate_price = fields.Float(
        string='Rate price',
        default=0.00,
    )
    rate_percentage = fields.Float(
        string='Rate %',
        default=0.00,
    )
    rate_qty_week = fields.Float(
        string='Rate quantity week',
        default=0.00,
    )
    rate_price_week = fields.Float(
        string='Rate price week',
        default=0.00,
    )
    rate_percentage_week = fields.Float(
        string='Rate % week',
        default=0.00,
    )
    rate_qty_month = fields.Float(
        string='Rate quantity month',
        default=0.00,
    )
    rate_price_month = fields.Float(
        string='Rate price monthr',
        default=0.00,
    )
    rate_percentage_month = fields.Float(
        string='Rate % month',
        default=0.00,
    )
    rate_qty_year = fields.Float(
        string='Rate quantity year',
        default=0.00,
    )
    rate_price_year = fields.Float(
        string='Rate price year',
        default=0.00,
    )
    rate_percentage_year = fields.Float(
        string='Rate % year',
        default=0.00,
    )

    @api.model
    def stock_move_search(self, company, date_from, date_to=None, product=None,
                          origin_usage=None, dest_usage=None, warehouse=None):
        domain = [
            ('company_id', '=', company.id),
            ('date', '>=', fields.Date.to_string(date_from)),
            ('date', '<=', fields.Date.to_string(date_to)),
            ('state', 'in', ['done', 'partially_available', 'assigned']),
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
        is_zero = (
            float_is_zero(qty_sale, precision_rounding=2)
            or float_is_zero((stock_init + stock_end), precision_rounding=2))
        if is_zero:
            result['rate_price'] = 0.00
            result['rate_qty'] = 0.00
            result['percentage'] = 0.00
            return result
        if not is_mrp:
            qty_sale += qty_production
        average_inventory = (stock_init + stock_end) / 2
        result['rate_qty'] = qty_sale / average_inventory
        result['percentage'] = round(((qty_sale / average_inventory) * 100), 0)
        if not float_is_zero(price, precision_rounding=2):
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
        products = self.env['product.product'].search([
            ('type', 'not in', ('consu', 'service')),
        ])
        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', company.id),
        ])
        for warehouse in warehouses:
            for product in products:
                is_stats = bool(self.search([
                    ('warehouse_id', '=', warehouse.id),
                    ('product_id', '=', product.id),
                    ('company_id', '=', company.id),
                    ('year', '=', date_from.year),
                    ('month', '=', date_from.month),
                    ('week', '=', date_to.isoweekday()),
                    ('day', '=', date_to.day),
                ], limit=1))
                if is_stats:
                    continue
                product_mrp = False
                if (product.product_tmpl_id._fields.get('bom_count', False)
                        and product.product_tmpl_id.bom_count != 0):
                    product_mrp = True
                sales_out_moves = self.stock_move_search(
                    company=company, date_from=date_from, date_to=date_to,
                    product=product, dest_usage='customer',
                    warehouse=warehouse)
                sales_in_moves = self.stock_move_search(
                    company=company, date_from=date_from, date_to=date_to,
                    product=product, origin_usage='customer',
                    warehouse=warehouse)
                purchase_out_moves = self.stock_move_search(
                    company=company, date_from=date_from, date_to=date_to,
                    product=product, dest_usage='supplier',
                    warehouse=warehouse)
                purchase_in_moves = self.stock_move_search(
                    company=company, date_from=date_from, date_to=date_to,
                    product=product, origin_usage='supplier',
                    warehouse=warehouse)
                if product_mrp is True:
                    production_out_moves = self.stock_move_search(
                        company=company, date_from=date_from,
                        date_to=date_to, product=product,
                        dest_usage='internal', origin_usage='production',
                        warehouse=warehouse)
                    production_in_moves = self.stock_move_search(
                        company=company, date_from=date_from,
                        date_to=date_to, product=product,
                        origin_usage='production', dest_usage='internal',
                        warehouse=warehouse)
                inventory_out_moves = self.stock_move_search(
                    company=company, date_from=date_from, date_to=date_to,
                    product=product, origin_usage='inventory',
                    dest_usage='internal', warehouse=warehouse)
                inventory_in_moves = self.stock_move_search(
                    company=company, date_from=date_from, date_to=date_to,
                    product=product, dest_usage='inventory',
                    origin_usage='internal', warehouse=warehouse)
                sales_moves = (round((
                    sum(sales_out_moves.mapped('product_uom_qty'))
                    - sum(sales_in_moves.mapped('product_uom_qty'))), 0))
                purchase_moves = (round((
                    sum(purchase_in_moves.mapped('product_uom_qty'))
                    - sum(purchase_out_moves.mapped('product_uom_qty'))), 0))
                inventory_moves = (round((
                    sum(inventory_out_moves.mapped('product_uom_qty'))
                    - sum(inventory_in_moves.mapped('product_uom_qty'))), 0))
                if product_mrp:
                    production_moves = (round((
                        sum(production_out_moves.mapped('product_uom_qty'))
                        - sum(production_in_moves.mapped(
                            'product_uom_qty'))), 0))
                else:
                    production_moves = 0
                domain = [
                    ('company_id', '=', company.id),
                    ('warehouse_id', '=', warehouse.id),
                    ('product_id', '=', product.id),
                    ('year', '=', date_to.year),
                    ('month', '=', date_to.month),
                    ('week', '=', date_to.isoweekday()),
                    ('day', '=', date_to.day),
                ]
                stat = self.search(domain, limit=1)
                if not stat.qty_stock_end:
                    qty_stock_init = inventory_moves
                else:
                    qty_stock_init = stat.qty_stock_end
                qty_stock_end = (qty_stock_init - sales_moves
                                 + purchase_moves + inventory_moves
                                 + production_moves)
                qty_move = qty_stock_end - qty_stock_init
                stats = self.calculate_rotation(
                    price=product.standard_price,
                    qty_sale=sales_moves, stock_init=qty_stock_init,
                    stock_end=qty_stock_end, is_mrp=product_mrp,
                    qty_production=production_moves)
                self.create({
                    'date_day': date_to,
                    'company_id': company.id,
                    'warehouse_id': warehouse.id,
                    'product_id': product.id,
                    'product_mrp': product_mrp,
                    'year': date_to.year,
                    'month': date_to.month,
                    'week': date_to.isoweekday(),
                    'day': date_to.day,
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

    @api.multi
    def compute_stock_rotation_day(self, init_date=None,
                                   end_date=None, company=None):
        _log.info('Start calculation statistics process')
        if not end_date:
            end_date = fields.Date.from_string(fields.Date.today())
        date_difference = relativedelta(end_date, init_date)
        number_days = (end_date - init_date).days
        compute_date = init_date + relativedelta(days=-1)
        while number_days > -1:
            self.compute_quantities_by_date(
                date_from=compute_date, date_to=compute_date,
                company=company)
            number_days -= 1
            compute_date += relativedelta(days=+1)
        if date_difference.weeks > 0:
            self.compute_stock_rotation_week(init_date, end_date, company)
        if date_difference.months > 0:
            self.compute_stock_rotation_month(init_date, end_date, company)
        if date_difference.years > 0:
            self.compute_stock_rotation_year(init_date, end_date, company)
        _log.info('End calculation statistics process')

    @api.multi
    def compute_stock_rotation_week(
            self, init_date=None, end_date=None, company=None):
        _log.info('Start calculation weekly statistics process')
        sql_query = '''
            SELECT
                ppsr.company_id,
                ppsr.warehouse_id,
                ppsr.product_id,
                ppsr.date_day,
                ppsr.year,
                ppsr.month,
                ppsr.week,
                SUM(ppsr.qty_sale) AS qty_sale,
                SUM(ppsr.qty_production) AS qty_production
            FROM
                product_product_stock_rotation AS ppsr
            WHERE
                date_day >= '%s' AND date_day <= '%s' AND company_id = %s
            GROUP BY
                ppsr.company_id,
                ppsr.warehouse_id,
                ppsr.product_id,
                ppsr.year,
                ppsr.month,
                ppsr.week,
                ppsr.date_day
            ORDER BY
                year ASC,
                month ASC,
                week ASC
         ''' % (fields.Date.to_string(init_date),
                fields.Date.to_string(end_date), company.id)
        self.env.cr.execute(sql_query)
        rotations = self.env.cr.dictfetchall()
        for rotation in rotations:
            stats = self.search([
                ('company_id', '=', rotation['company_id']),
                ('warehouse_id', '=', rotation['warehouse_id']),
                ('product_id', '=', rotation['product_id']),
                ('year', '=', rotation['year']),
                ('month', '=', rotation['month']),
                ('week', '=', rotation['week']),
            ])
            week_init = stats[0]
            week_end = stats[-1]
            if not week_init or not week_end:
                continue
            price = (week_init.standard_price + week_end.standard_price) / 2
            week_rates = self.calculate_rotation(
                price=price,
                qty_sale=rotation['qty_sale'],
                qty_production=rotation['qty_production'],
                stock_init=week_init['qty_stock_init'],
                stock_end=week_end['qty_stock_end'],
                is_mrp=week_end['product_mrp'],
            )
            for stat in stats:
                stat.write({
                    'rate_price_week': week_rates['rate_price'],
                    'rate_qty_week': week_rates['rate_qty'],
                    'rate_percentage_week': week_rates['percentage'],
                })
        _log.info('End calculation weekly statistics process')

    @api.multi
    def compute_stock_rotation_month(
            self, init_date=None, end_date=None, company=None):
        _log.info('Start calculation month statistics process')
        sql_query = '''
            SELECT
                ppsr.company_id,
                ppsr.warehouse_id,
                ppsr.product_id,
                ppsr.date_day,
                ppsr.year,
                ppsr.month,
                SUM(ppsr.qty_sale) AS qty_sale,
                SUM(ppsr.qty_production) AS qty_production
            FROM
                product_product_stock_rotation ppsr
            WHERE
                date_day >= '%s' AND date_day <= '%s' AND company_id = %s
            GROUP BY
                ppsr.company_id,
                ppsr.warehouse_id,
                ppsr.product_id,
                ppsr.year,
                ppsr.month,
                ppsr.date_day
            ORDER BY
                year ASC,
                month ASC
        ''' % (init_date, end_date, company.id)
        self.env.cr.execute(sql_query)
        rotations = self.env.cr.dictfetchall()
        for rotation in rotations:
            stats = self.search([
                ('company_id', '=', rotation['company_id']),
                ('warehouse_id', '=', rotation['warehouse_id']),
                ('product_id', '=', rotation['product_id']),
                ('year', '=', rotation['year']),
                ('month', '=', rotation['month']),
            ])
            month_init = stats[0]
            month_end = stats[-1]
            if not month_init or not month_end:
                continue
            price = (month_init.standard_price + month_end.standard_price) / 2
            month_rates = self.calculate_rotation(
                price=price,
                qty_sale=rotation['qty_sale'],
                qty_production=rotation['qty_production'],
                stock_init=month_init['qty_stock_init'],
                stock_end=month_end.qty_stock_end,
                is_mrp=month_end.product_mrp,
            )
            for stat in stats:
                stat.write({
                    'rate_price_month': month_rates['rate_price'],
                    'rate_qty_month': month_rates['rate_qty'],
                    'rate_percentage_month': month_rates['percentage'],
                })
        _log.info('End calculation month statistics process')

    @api.multi
    def compute_stock_rotation_year(
            self, init_date=None, end_date=None, company=None):
        _log.info('Start calculation year statistics process')
        sql_query = '''
            SELECT
                ppsr.company_id,
                ppsr.warehouse_id,
                ppsr.product_id,
                ppsr.date_day,
                ppsr.year,
                SUM(ppsr.qty_sale) AS qty_sale,
                SUM(ppsr.qty_production) AS qty_production
            FROM
                product_product_stock_rotation ppsr
            WHERE
                date_day >= '%s' AND date_day <= '%s' AND company_id = %s
            GROUP BY
                ppsr.company_id,
                ppsr.warehouse_id,
                ppsr.product_id,
                ppsr.year,
                ppsr.date_day
            ORDER BY
                year ASC
        ''' % (init_date, end_date, company.id)
        self.env.cr.execute(sql_query)
        rotations = self.env.cr.dictfetchall()
        for rotation in rotations:
            stats = self.search([
                ('company_id', '=', rotation['company_id']),
                ('warehouse_id', '=', rotation['warehouse_id']),
                ('product_id', '=', rotation['product_id']),
                ('year', '=', rotation['year']),
            ])
            year_init = stats[0]
            year_end = stats[-1]
            if not year_end or not year_init:
                continue
            price = (year_init.standard_price + year_end.standard_price) / 2
            year_rates = self.calculate_rotation(
                price=price,
                qty_sale=rotation['qty_sale'],
                qty_production=rotation['qty_production'],
                stock_init=year_init.qty_stock_init,
                stock_end=year_end.qty_stock_end,
                is_mrp=year_end.product_mrp,
            )
            for stat in stats:
                stat.write({
                    'rate_price_year': year_rates['rate_price'],
                    'rate_qty_year': year_rates['rate_qty'],
                    'rate_percentage_year': year_rates['percentage'],
                })
        _log.info('End calculation year statistics process')

    @api.multi
    def cron_run_compute_stock_rotation_day(self):
        companies = self.env['res.company'].search([
            ('is_stock_rotation', '=', True),
        ])
        today = fields.Date.from_string(fields.Date.today())
        for company in companies:
            if company.rotation_init_date:
                init_date = fields.Date.from_string(company.rotation_init_date)
                self.compute_stock_rotation_day(
                    init_date=init_date, end_date=None, company=company)
            else:
                self.compute_stock_rotation_day(
                    init_date=today, end_date=None, company=company)
