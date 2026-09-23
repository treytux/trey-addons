###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    use_management = fields.Boolean(
        string='Use management',
    )
    qc_test_ids = fields.Many2many(
        string='Tests',
        comodel_name='qc.test',
        relation='qc_test2product_template_rel',
        column1='product_id',
        column2='qc_test_id',
    )

    def get_product_qc_use_date(self, product_tmpl):
        return self.env['qc.use.date'].search([
            ('product_tmpl_id', '=', product_tmpl.id),
        ], order='date desc, id').ids

    def action_view_product_qc_use_date(self):
        qc_use_date_ids = self.get_product_qc_use_date(self)
        form_view = self.env.ref(
            'product_use_management.qc_use_date_form_view')
        tree_view = self.env.ref(
            'product_use_management.qc_use_date_tree_view')
        search_view = self.env.ref(
            'product_use_management.qc_use_date_search_view')
        action_vals = {
            'name': _('Use management'),
            'res_model': 'qc.use.date',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', qc_use_date_ids)],
        }
        if len(qc_use_date_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': qc_use_date_ids[0],
            })
        return action_vals
