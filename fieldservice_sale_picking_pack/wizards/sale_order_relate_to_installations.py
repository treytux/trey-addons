###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderRelateToInstallation(models.TransientModel):
    _name = 'sale.order.relate_to_installations'
    _description = 'Wizard for relate products with installations'

    name = fields.Char(
        string='Empty',
    )
    line_ids = fields.One2many(
        comodel_name='sale.order.relate_to_installations.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        sale = self.env['sale.order'].browse(
            self.env.context.get('active_id', []))
        sale_lines_not_installation = sale.order_line.filtered(
            lambda ln: ln.product_id.type != 'service'
            and ln.product_id.installation_product is False)
        relate_to_install_lines_ids = []
        for sale_line_not_installation in sale_lines_not_installation:
            line = self.env['sale.order.relate_to_installations.line'].create({
                'wizard_id': self.id,
                'sale_line_id': sale_line_not_installation.id,
                'sale_line_fsm_id': (
                    sale_line_not_installation.sale_line_fsm_id.id),
            })
            relate_to_install_lines_ids.append(line.id)
        res['line_ids'] = [(6, 0, relate_to_install_lines_ids)]
        return res

    def button_accept(self):
        self.ensure_one()
        for line in self.line_ids:
            line.sale_line_id.sale_line_fsm_id = (
                line.sale_line_fsm_id and line.sale_line_fsm_id.id or None)


class SaleOrderRelateToInstallationLine(models.TransientModel):
    _name = 'sale.order.relate_to_installations.line'
    _description = 'Wizard lines'

    @api.model
    def _get_domain_sale_line_fsm_id(self):
        model = self._context.get('active_model')
        sale_id = self._context.get('active_id')
        if not model or not sale_id:
            return []
        sale = self.env[model].browse(sale_id)
        sale_lines = sale.order_line.filtered(
            lambda ln: ln.product_id.installation_product is True)
        return [
            ('id', 'in', sale_lines.ids),
            ('product_id.field_service_tracking', '!=', 'no'),
            ('product_id.installation_product', '=', True),
        ]

    name = fields.Char(
        string='Empty',
    )
    wizard_id = fields.Many2one(
        comodel_name='sale.order.relate_to_installations',
        string='Wizard',
    )
    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line',
        readonly=True,
    )
    sale_line_fsm_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Related with',
        domain=_get_domain_sale_line_fsm_id,
        help='Product line installation with which it is related. It is used '
             'so that this product is added to the fsm order of the related '
             'product when the sales order is confirmed.\nUse the "Relate to '
             'installations" wizard to map them if you need to.'
    )
