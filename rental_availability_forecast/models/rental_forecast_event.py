##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import fields, models, tools


class RentalForecastEvent(models.Model):

    _name = 'rental.forecast.event'
    _description = 'Rental forecast events'
    _auto = False
    _order = 'event_date, id'
    _rec_name = 'event_date'

    event_date = fields.Date(
        string='Date',
        readonly=True,
    )
    event_type = fields.Selection(
        selection=[
            ('rental_start', 'Rental start'),
            ('rental_return', 'Rental return'),
            ('confirmed_rental', 'Confirmed rental'),
            ('stock_out', 'Stock outgoing'), ],
        string='Event Type',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    quantity_change = fields.Float(
        string='Units',
        digits='Product unit of measure',
        readonly=True,
    )
    rental_id = fields.Many2one(
        comodel_name='sale.rental',
        string='Rental',
        readonly=True,
    )
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line',
        readonly=True,
    )
    stock_move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock move',
        readonly=True,
    )
    description = fields.Char(
        string='Description',
        readonly=True,
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            '''
            CREATE VIEW rental_forecast_event AS (
                SELECT
                    row_number() OVER (
                        ORDER BY event_date, product_id,
                        warehouse_id, event_type, source_id
                    ) AS id,
                    event_date,
                    event_type,
                    product_id,
                    warehouse_id,
                    company_id,
                    quantity_change,
                    rental_id,
                    sale_order_line_id,
                    stock_move_id,
                    description
                FROM (
                    SELECT
                        GREATEST(r.start_date, CURRENT_DATE) AS event_date,
                        'rental_start' AS event_type,
                        r.rented_product_id AS product_id,
                        sol.order_id AS warehouse_id_source,
                        so.warehouse_id,
                        r.company_id,
                        -r.rental_qty AS quantity_change,
                        r.id AS rental_id,
                        r.start_order_line_id AS sale_order_line_id,
                        NULL::integer AS stock_move_id,
                        'Rental start' AS description,
                        r.id AS source_id
                    FROM sale_rental r
                    JOIN sale_order_line sol ON sol.id = r.start_order_line_id
                    JOIN sale_order so ON so.id = sol.order_id
                    WHERE r.state NOT IN ('cancel', 'in')
                      AND r.end_date >= CURRENT_DATE

                    UNION ALL

                    SELECT
                        r.end_date + 1 AS event_date,
                        'rental_return' AS event_type,
                        r.rented_product_id AS product_id,
                        sol.order_id AS warehouse_id_source,
                        so.warehouse_id,
                        r.company_id,
                        r.rental_qty AS quantity_change,
                        r.id AS rental_id,
                        r.start_order_line_id AS sale_order_line_id,
                        NULL::integer AS stock_move_id,
                        'Rental return' AS description,
                        r.id AS source_id
                    FROM sale_rental r
                    JOIN sale_order_line sol ON sol.id = r.start_order_line_id
                    JOIN sale_order so ON so.id = sol.order_id
                    WHERE r.state NOT IN ('cancel', 'in', 'sold')
                      AND r.end_date + 1 >= CURRENT_DATE

                    UNION ALL

                    SELECT
                        GREATEST(sol.start_date, CURRENT_DATE) AS event_date,
                        'confirmed_rental' AS event_type,
                        pp.rented_product_id AS product_id,
                        sol.order_id AS warehouse_id_source,
                        so.warehouse_id,
                        so.company_id,
                        -sol.rental_qty AS quantity_change,
                        NULL::integer AS rental_id,
                        sol.id AS sale_order_line_id,
                        NULL::integer AS stock_move_id,
                        'Confirmed rental line' AS description,
                        sol.id AS source_id
                    FROM sale_order_line sol
                    JOIN sale_order so ON so.id = sol.order_id
                    JOIN product_product pp ON pp.id = sol.product_id
                    WHERE so.state IN ('sale', 'done')
                      AND sol.rental_type IN ('new_rental', 'rental_extension')
                      AND sol.end_date >= CURRENT_DATE
                      AND NOT EXISTS (
                          SELECT 1 FROM sale_rental r
                          WHERE r.start_order_line_id = sol.id
                      )

                    UNION ALL

                    SELECT
                        sm.date::date AS event_date,
                        'stock_out' AS event_type,
                        sm.product_id,
                        NULL::integer AS warehouse_id_source,
                        sw.id AS warehouse_id,
                        sm.company_id,
                        -sm.product_uom_qty AS quantity_change,
                        NULL::integer AS rental_id,
                        sm.sale_line_id AS sale_order_line_id,
                        sm.id AS stock_move_id,
                        'Confirmed stock outgoing' AS description,
                        sm.id AS source_id
                    FROM stock_move sm
                    JOIN stock_warehouse sw
                      ON sw.company_id = sm.company_id
                    JOIN stock_location src ON src.id = sm.location_id
                    JOIN stock_location dst ON dst.id = sm.location_dest_id
                    JOIN stock_location rin
                      ON rin.id = sw.rental_in_location_id
                    WHERE sm.state IN ('confirmed', 'waiting',
                    'partially_available', 'assigned')
                      AND sm.date::date >= CURRENT_DATE
                      AND (
                      src.id = rin.id OR src.parent_path
                        LIKE rin.parent_path || '%')
                      AND NOT (
                      dst.id = rin.id OR dst.parent_path
                        LIKE rin.parent_path || '%')
                      AND NOT EXISTS (
                          SELECT 1
                          FROM sale_order_line draft_sol
                          JOIN sale_order draft_so
                          ON draft_so.id = draft_sol.order_id
                          WHERE draft_sol.id = sm.sale_line_id
                            AND draft_so.state IN ('draft', 'sent')
                      )
                      AND NOT EXISTS (
                          SELECT 1 FROM sale_rental r
                          WHERE r.out_move_id = sm.id
                      )
                ) events
                WHERE warehouse_id IS NOT NULL
            )
            ''')

    def action_open_source(self):
        self.ensure_one()
        if self.rental_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.rental',
                'res_id': self.rental_id.id,
                'view_mode': 'form', }
        if self.sale_order_line_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': self.sale_order_line_id.order_id.id,
                'view_mode': 'form', }
        if self.stock_move_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.move',
                'res_id': self.stock_move_id.id,
                'view_mode': 'form', }
        return False
