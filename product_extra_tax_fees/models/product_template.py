###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tax_fee_ids = fields.One2many(
        comodel_name='account.tax.fee',
        string='Extra taxes',
        compute='_compute_tax_fee_ids',
    )

    def _compute_tax_fee_ids(self):
        for product_tmp in self:
            product_tmp.tax_fee_ids = self.env['account.tax.fee'].search([
                '|',
                ('product_tmpl_ids', 'in', product_tmp.ids),
                ('apply_on', '=', 'all'),
            ]).ids

    def get_tax_fees(self, partner_id):
        self.ensure_one()
        tax_fees = self.tax_fee_ids.filtered(
            lambda t: t.country_id == partner_id.country_id)
        return tax_fees

    def action_view_tax_fees(self):
        form_view = self.env.ref(
            'product_extra_tax_fees.account_tax_fee_form_view')
        tree_view = self.env.ref(
            'product_extra_tax_fees.account_tax_fee_tree_view')
        action_vals = {
            'name': _('Tax fees'),
            'res_model': 'account.tax.fee',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': self.env.ref(
                'product_extra_tax_fees.account_tax_fee_search_view').id,
            'view_type': 'form',
            'domain': [('id', 'in', self.tax_fee_ids.ids)],
        }
        if len(self.tax_fee_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': self.tax_fee_ids[0].id,
            })
        return action_vals
