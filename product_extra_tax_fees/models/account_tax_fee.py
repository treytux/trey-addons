###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AccountTaxFee(models.Model):
    _name = 'account.tax.fee'
    _description = 'Account tax fee'

    name = fields.Char(
        required=True,
    )
    amount = fields.Float()
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        string='Product templates',
        relation='tax_fee2product_tmpl_rel',
        column1='tax_fee_id',
        column2='product_tmpl_id',
    )
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        required=True,
    )
    apply_on = fields.Selection(
        selection=[
            ('all', 'All'),
            ('selected_products', 'Selected products'),
        ],
        string='Apply on',
        default='all',
        required=True,
    )
    compute_method = fields.Selection(
        selection=[
            ('fixed', 'Fixed price'),
            ('formula', 'Formula'),
        ],
        string='Compute method',
        default='fixed',
        required=True,
    )
    formula = fields.Text(
        string='Formula',
    )
    show_on_invoice = fields.Selection(
        selection=[
            ('always', 'Always'),
            ('value', 'If tax value'),
            ('never', 'Never'),
        ],
        string='Show on invoice',
        help='Show fee amount on invoices',
        default='value',
        required=True,
    )

    @api.onchange('compute_method')
    def _onchange_compute_method(self):
        for tax in self:
            tax.formula = ''
            tax.amount = 0.0

    @api.onchange('apply_on')
    def _onchange_apply_on(self):
        for tax in self:
            tax.product_tmpl_ids = False

    def get_tax_fee(self, fee_line, quantity):
        self.ensure_one()
        if not fee_line.product_id or not fee_line.partner_id:
            return 0
        if self.compute_method == 'fixed':
            return self.amount * quantity
        elif self.compute_method == 'formula':
            try:
                res = eval(self.formula)
            except Exception:
                results = fee_line._get_formula_input_dict(self)
                safe_eval(self.formula, results, mode='exec', nocopy=True)
                return float(results['result'])
            return (float(res) * quantity)
