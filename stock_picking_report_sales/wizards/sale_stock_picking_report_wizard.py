##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo.exceptions import UserError
from odoo import models, api, _


class SaleStockPickingReportWizard(models.TransientModel):
    _name = 'sale.stock.picking.report_wizard'
    _description = 'Wizard to report sale orders from stock pickings'

    def get_sale_orders(self, stock_pickings):
        sales = self.env['sale.order']
        for picking in stock_pickings:
            if picking.sale_id and picking.sale_id not in sales:
                sales |= picking.sale_id
        return sales

    @api.multi
    def button_accept(self):
        self.ensure_one()
        active_ids = self.env.context['active_ids']
        if not active_ids:
            raise UserError(_('You must select at least one stock picking'))
        stock_pickings = self.env['stock.picking'].browse(active_ids)
        sales = self.get_sale_orders(stock_pickings)
        if not sales:
            raise UserError(
                _('Selected stock picking do not have sale order associated'))
        report = self.env.ref('sale.action_report_saleorder')
        return report.report_action(sales)
