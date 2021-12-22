###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    quantity_available = fields.Float(
        string='Quantity On Hand',
        readonly=True,
    )
    virtual_available = fields.Float(
        string='Virtual available',
        readonly=True,
    )
    stock_location = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        readonly=True,
    )

    def _from(self):
        return '%s LEFT JOIN stock_quant q ON q.product_id = ail.product_id' % (
            super()._from())

    def _sub_select(self):
        return '''
            %s,
            q.quantity as quantity_available,
            q.location_id as stock_location,
            SUM(q.quantity - q.reserved_quantity) as virtual_available
            ''' % super()._sub_select()

    def _select(self):
        return '''
            %s,
            sub.quantity_available as quantity_available,
            sub.stock_location as stock_location,
            sub.virtual_available as virtual_available
        ''' % super()._select()

    def _group_by(self):
        return '%s, q.quantity, q.location_id' % super()._group_by()
