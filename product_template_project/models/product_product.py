###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_view_projects(self):
        self.ensure_one()
        action = self.env.ref(
            'product_template_project.act_product_project_view').read()[0]
        if len(self.product_tmpl_id.project_ids) > 0:
            action['domain'] = [
                ('id', 'in', self.product_tmpl_id.project_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
