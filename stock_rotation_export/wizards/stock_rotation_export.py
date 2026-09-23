###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from pytz import UTC, timezone

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class StockRotationExport(models.TransientModel):
    _name = 'stock.rotation.export'
    _description = 'Export stock rotation'

    step = fields.Integer(
        string='Step',
        default=0,
    )
    data_file = fields.Binary(
        string='File',
    )
    file_filename = fields.Char(
        string='Filename',
    )
    date_from = fields.Datetime(
        string='Date from',
        required=True,
    )
    date_to = fields.Datetime(
        string='Date to',
        required=True,
        default=fields.Datetime.now,
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        domain="[('supplier', '=', True)]",
    )

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for wizard in self:
            now = fields.Datetime.now()
            if wizard.date_from > now or wizard.date_to > now:
                raise ValidationError(_(
                    'Dates must not be later than the current date.'))
            if wizard.date_from > wizard.date_to:
                raise ValidationError(_(
                    'The "From date" must be less than the "To date".'))

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def _get_product_ids(self):
        supplierinfos = self.env['product.supplierinfo'].search([
            ('name', '=', self.supplier_id.id),
        ])
        products = supplierinfos.mapped('product_id')
        products |= supplierinfos.mapped('product_tmpl_id.product_variant_ids')
        if not products:
            raise ValidationError(_(
                'No product associated with the selected supplier \'%s\' has '
                'been found.') % self.supplier_id.name)
        return products.ids

    def _get_sql_select_clause(self):
        return '''
            WITH
                buyer_sql AS (
                    SELECT
                        sm.product_id,
                        sm.location_dest_id as location,
                        SUM(sm.product_uom_qty)
                        *
                        (CASE
                            WHEN sl_dst.usage = 'internal'
                                THEN 1
                            ELSE 0
                        END) AS suma
                    FROM stock_move AS sm
                    LEFT JOIN stock_location AS sl_dst
                       ON sm.location_dest_id = sl_dst.id
                    WHERE
                        sm.location_id IN (
                            SELECT id
                            FROM stock_location
                            WHERE usage = 'supplier'
                        )
                        AND product_id = sm.product_id
                        AND date >= %s
                        AND date <= %s
                    GROUP BY
                        sm.product_id,
                        location,
                        sl_dst.usage
                ),
                customer_return_sql AS (
                    SELECT
                        sm.product_id,
                        sm.location_dest_id as location,
                        SUM(sm.product_uom_qty)
                        *
                        (CASE
                            WHEN sl_dst.usage = 'internal'
                                THEN 1
                            ELSE 0
                        END) AS suma
                    FROM stock_move AS sm
                    LEFT JOIN stock_location AS sl_dst
                       ON sm.location_dest_id = sl_dst.id
                    WHERE
                        sm.location_id IN (
                            SELECT id
                            FROM stock_location
                            WHERE usage = 'customer'
                        )
                        AND product_id = sm.product_id
                        AND date >= %s
                        AND date <= %s
                    GROUP BY
                        sm.product_id,
                        location,
                        sl_dst.usage
                ),
                sold_sql AS (
                    SELECT
                        sm.product_id,
                        sm.location_id as location,
                        SUM(sm.product_uom_qty)
                        *
                        (CASE
                            WHEN sl_src.usage = 'internal'
                                THEN 1
                            ELSE 0
                        END) AS suma
                    FROM stock_move AS sm
                    LEFT JOIN stock_location AS sl_src
                        ON sm.location_id = sl_src.id
                    WHERE
                        sm.location_dest_id IN (
                            SELECT id
                            FROM stock_location
                            WHERE usage = 'customer'
                        )
                        AND product_id = sm.product_id
                        AND date >= %s
                        AND date <= %s
                    GROUP BY
                        sm.product_id,
                        location,
                        sl_src.usage
                ),
                supplier_return_sql AS (
                    SELECT
                        sm.product_id,
                        sm.location_id as location,
                        SUM(sm.product_uom_qty)
                        *
                        (CASE
                            WHEN sl_src.usage = 'internal'
                                THEN 1
                            ELSE 0
                        END) AS suma
                    FROM stock_move AS sm
                    LEFT JOIN stock_location AS sl_src
                        ON sm.location_id = sl_src.id
                    WHERE
                        sm.location_dest_id IN (
                            SELECT id
                            FROM stock_location
                            WHERE usage = 'supplier'
                        )
                        AND product_id = sm.product_id
                        AND date >= %s
                        AND date <= %s
                    GROUP BY
                        sm.product_id,
                        location,
                        sl_src.usage
                )
            SELECT
                move.product_id,
                location_id,
                COALESCE((
                    buyer_sql.suma
                ), 0) AS buyer,
                COALESCE((
                    customer_return_sql.suma
                ), 0) AS customer_return,
                COALESCE((
                    sold_sql.suma
                ), 0) AS sold,
                COALESCE((
                    supplier_return_sql.suma
                ), 0) AS supplier_return
        '''

    def _get_sql_from_clause(self):
        return '''
            FROM stock_move AS move
            LEFT JOIN buyer_sql
                ON move.product_id = buyer_sql.product_id
                AND move.location_id = buyer_sql.location
            LEFT JOIN customer_return_sql
                ON move.product_id = customer_return_sql.product_id
                AND move.location_id = customer_return_sql.location
            LEFT JOIN sold_sql
                ON move.product_id = sold_sql.product_id
                AND move.location_id = sold_sql.location
            LEFT JOIN supplier_return_sql
                ON move.product_id = supplier_return_sql.product_id
                AND move.location_id = supplier_return_sql.location
        '''

    def _get_sql_where_clause(self):
        res = '''
            WHERE
                (company_id = %s
                OR
                company_id IS null)
        '''
        if self.supplier_id:
            res_supplier = '''
                AND move.product_id in %s
            '''
            res += res_supplier
        return res

    def _get_sql_group_by_clause(self):
        return '''
            GROUP BY
                move.product_id,
                location_id,
                buyer_sql.suma,
                customer_return_sql.suma,
                sold_sql.suma,
                supplier_return_sql.suma
        '''

    def _get_sql_params(self):
        params = [
            self.date_from, self.date_to,
            self.date_from, self.date_to,
            self.date_from, self.date_to,
            self.date_from, self.date_to,
            self.env.user.company_id.id
        ]
        if self.supplier_id:
            product_ids = tuple(self._get_product_ids())
            params.append(product_ids)
        return tuple(params)

    def get_basic_columns(self, line_id):
        product = self.env['product.product'].browse(line_id[0])
        location = self.env['stock.location'].browse(line_id[1])
        buyed = line_id[2]
        customer_return = line_id[3]
        sold = line_id[4]
        supplier_return = line_id[5]
        qty_available_date_from = product.with_context(
            location=location.id,
            to_date=self.date_from
        ).qty_available
        qty_available_date_to = product.with_context(
            location=location.id,
            to_date=self.date_to
        ).qty_available
        ratio = round((
            (buyed + customer_return + qty_available_date_from)
            / (sold + supplier_return)
        ), 2) if (sold + supplier_return) else 0
        return {
            'product': product,
            'location': location,
            'buyed': buyed,
            'customer_return': customer_return,
            'sold': sold,
            'supplier_return': supplier_return,
            'qty_available_date_from': qty_available_date_from,
            'qty_available_date_to': qty_available_date_to,
            'ratio': ratio,
        }

    def get_data_row(self, columns_dict):
        product = columns_dict['product']
        location = columns_dict['location']
        ratio = columns_dict['ratio']
        qty_available_date_from = columns_dict['qty_available_date_from']
        qty_available_date_to = columns_dict['qty_available_date_to']
        buyed = columns_dict['buyed']
        customer_return = columns_dict['customer_return']
        sold = columns_dict['sold']
        supplier_return = columns_dict['supplier_return']
        return {
            _('Product default code'): product.default_code,
            _('Product name'): product.name,
            _('Category'): product.categ_id.complete_name,
            _('Location'): location.complete_name,
            _('Ratio'): ratio,
            _('Stock in date from'): qty_available_date_from,
            _('Stock in date to'): qty_available_date_to,
            _('Buyed'): buyed,
            _('Customer return'): customer_return,
            _('Sold'): sold,
            _('Supplier return'): supplier_return,
        }

    def get_rows(self):
        sql = self._get_sql_select_clause()
        sql += self._get_sql_from_clause()
        sql += self._get_sql_where_clause()
        sql += self._get_sql_group_by_clause()
        params = self._get_sql_params()
        self.env.cr.execute(sql, params)
        rows = []
        line_ids = self.env.cr.fetchall()
        while line_ids:
            some_line_ids = line_ids[:1000]
            line_ids = line_ids[1000:]
            for line_id in some_line_ids:
                sql_columns_dict = self.get_basic_columns(line_id)
                data_dict = self.get_data_row(sql_columns_dict)
                rows.append(data_dict)
        return rows

    def write_file(self, rows):
        df = pd.DataFrame(rows)
        to_write = io.BytesIO()
        df.to_excel(to_write, index=False, engine='xlsxwriter')
        to_write.seek(0)
        return to_write

    def generate_file(self):
        rows = self.get_rows()
        return self.write_file(rows)

    def get_datas(self, model, domain):
        return self.env[model].search(domain)

    def get_filename(self):
        tz = timezone(self.env.user.tz)
        date_from_tz = self.date_from.replace(tzinfo=UTC).astimezone(tz).date()
        format_from = date_from_tz.strftime('%y%m%d')
        date_to_tz = self.date_to.replace(tzinfo=UTC).astimezone(tz).date()
        format_to = date_to_tz.strftime('%y%m%d')
        return f'stock_rotation_{format_from}_{format_to}'

    def action_accept(self):
        to_write = self.generate_file()
        self.file_filename = self.get_filename()
        self.data_file = base64.b64encode(to_write.getvalue())
        self.step = 1
        return self._reopen_view()
