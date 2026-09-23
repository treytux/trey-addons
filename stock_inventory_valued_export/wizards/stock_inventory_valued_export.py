###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

from odoo import _, fields, models

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class StockInventoryValuedExport(models.TransientModel):
    _name = 'stock.inventory.valued.export'
    _description = 'Export inventory valued'

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
    compute_at_date = fields.Selection(
        selection=[
            (0, 'Current inventory'),
            (1, 'At a specific date')
        ],
        string='Compute',
        help='Choose to analyze the current inventory or from a specific date '
             'in the past.'
    )
    date = fields.Datetime(
        string='Inventory at Date',
        help='Choose a date to get the inventory at that date',
        default=fields.Datetime.now,
    )

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

    def get_dict(self, product, location, qty_available):
        default_code = (
            '[%s] ' % product.default_code if product.default_code else '')
        return {
            _('Product'): '%s%s' % (default_code, product.name),
            _('Product category'): product.categ_id.complete_name,
            _('Location'): location.complete_name,
            _('Quantity'): qty_available,
            _('Standard price'): product.standard_price,
            _('Subtotal'): qty_available * product.standard_price,
        }

    def get_sql(self):
        return '''
            SELECT DISTINCT m.product_id
            FROM stock_move AS m
            LEFT JOIN stock_location AS l ON m.location_dest_id = l.id
            LEFT JOIN product_product AS p ON m.product_id = p.id
            LEFT JOIN product_template AS pt ON p.product_tmpl_id = pt.id
            WHERE
                l.usage = 'internal'
                AND pt.type = 'product'
                AND (
                    m.company_id = %s
                    OR
                    m.company_id IS NULL
                )
        '''

    def get_rows(self, locations):
        sql = self.get_sql()
        params = [self.env.user.company_id.id]
        if self.date:
            sql += 'AND m.date <= %s'
            params.append(self.date)
        self.env.cr.execute(sql, params)
        product_ids = [p_id[0] for p_id in self.env.cr.fetchall()]
        rows = []
        total = 0
        products = self.env['product.product'].browse(product_ids)
        while products:
            some_products = products[:1000]
            products = products[1000:]
            for product in some_products:
                for location in locations:
                    qty_available = product.with_context(
                        location=location.id,
                        to_date=self.date
                    ).qty_available
                    if qty_available <= 0:
                        continue
                    data_dict = self.get_dict(product, location, qty_available)
                    rows.append(data_dict)
                    total += data_dict['Subtotal']
        return rows, total

    def get_columns(self):
        return [
            _('Product'), _('Product category'), _('Location'),
            _('Quantity'), _('Standard price'), _('Subtotal')]

    def write_file(self, rows, total):
        df = pd.DataFrame(rows)
        total_list = ['', '', '', '', 'Total', total]
        df = df.append(pd.DataFrame(
            [total_list],
            columns=self.get_columns()),
            ignore_index=True)
        to_write = io.BytesIO()
        df.to_excel(to_write, index=False, engine='xlsxwriter')
        to_write.seek(0)
        return to_write

    def generate_file(self, locations):
        rows, total = self.get_rows(locations)
        return self.write_file(rows, total)

    def action_accept(self):
        locations = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            '|',
            ('company_id', '=', self.env.user.company_id.id),
            ('company_id', '=', None),
        ])
        to_write = self.generate_file(locations)
        self.data_file = base64.b64encode(to_write.getvalue())
        self.step = 1
        return self._reopen_view()
