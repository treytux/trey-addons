###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_partner_subvention(self):
        self.ensure_one()
        return self.env['partner.subvention'].search([
            ('partner_id', '=', self.id),
        ])

    def action_view_partner_subvention(self):
        partner_subvention = self.get_partner_subvention()
        form_view = self.env.ref(
            'partner_subvention.partner_subvention_form_view')
        tree_view = self.env.ref(
            'partner_subvention.partner_subvention_tree_view')
        pivot_view = self.env.ref(
            'partner_subvention.partner_subvention_pivot_view')
        action_vals = {
            'name': _('Partner subvention'),
            'res_model': 'partner.subvention',
            'type': 'ir.actions.act_window',
            'views': [
                (tree_view.id, 'tree'), (form_view.id, 'form'),
                (pivot_view.id, 'pivot')],
            'view_mode': 'tree, form',
            'view_type': 'form',
            'domain': [('id', 'in', partner_subvention.ids)],
        }
        if len(partner_subvention) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': partner_subvention.ids[0],
            })
        return action_vals
