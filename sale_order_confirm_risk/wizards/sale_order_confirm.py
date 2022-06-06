###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderConfirm(models.TransientModel):
    _inherit = 'sale.order.confirm'

    line_ids = fields.One2many(
        comodel_name='sale.order.confirm.line',
        inverse_name='wizard_id',
        string='Lines'
    )
    financial_risk_line_ids = fields.One2many(
        comodel_name='sale.order.confirm.line.risk',
        inverse_name='wizard_id',
        string='Lines with financial risk',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'line_ids' not in res:
            res['line_ids'] = []
        if 'financial_risk_line_ids' not in res:
            res['financial_risk_line_ids'] = []
        sales = self.env['sale.order'].browse(
            self.env.context.get('active_ids', []))
        lines = self.env['sale.order.confirm.line']
        lines_risk = self.env['sale.order.confirm.line.risk']
        for sale in sales:
            line_data = {
                'wizard_id': self.id,
                'sale_id': sale.id,
                'partner_id': sale.partner_id.id,
                'amount_total': sale.amount_total,
                'is_confirm': False,
            }
            exception_msg = sale.risk_exception_msg()
            if exception_msg:
                lines_risk |= lines_risk.create(line_data)
                continue
            line_data['is_confirm'] = True
            lines |= lines.create(line_data)
        res.update({
            'line_ids': [(6, 0, lines.ids)],
            'financial_risk_line_ids': [(6, 0, lines_risk.ids)]
        })
        return res

    def button_accept(self):
        self.ensure_one()
        if len(self.financial_risk_line_ids) == 0:
            return super().button_accept()
        for line in self.line_ids:
            line.sale_id.action_confirm()
        for line in self.financial_risk_line_ids:
            if line.is_confirm:
                line.sale_id.with_context(bypass_risk=True).action_confirm()
        return {'type': 'ir.actions.act_window_close'}


class SaleOrderConfirmLine(models.TransientModel):
    _name = 'sale.order.confirm.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='sale.order.confirm',
        string='Wizard',
    )
    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    amount_total = fields.Float(
        string='Amount total',
    )
    is_confirm = fields.Boolean(
        string='Confirm sale order',
    )


class SaleOrderConfirmLineRisk(models.TransientModel):
    _name = 'sale.order.confirm.line.risk'
    _description = 'Wizard lines risk'

    wizard_id = fields.Many2one(
        comodel_name='sale.order.confirm',
        string='Wizard',
    )
    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    amount_total = fields.Float(
        string='Amount total',
    )
    is_confirm = fields.Boolean(
        string='Confirm sale order',
    )
