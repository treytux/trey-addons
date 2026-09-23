###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_user = fields.Boolean(
        string='Is user?',
        tracking=True,
    )
    is_partner_full_member = fields.Boolean(
        string='Is partner full member?',
        tracking=True,
    )
    is_partner_collaborator = fields.Boolean(
        string='Is partner collaborator?',
        tracking=True,
    )
    is_family = fields.Boolean(
        string='Is family?',
        tracking=True,
    )

    def get_protected_data(self, partner):
        return self.env['partner.protected.data'].search([
            ('partner_id', '=', partner.id),
        ])

    def get_info_data(self, partner):
        return self.env['partner.info.data'].search([
            ('partner_id', '=', partner.id),
        ])

    def get_partner_history(self, partner):
        return self.env['partner.history'].search([
            ('partner_id', '=', partner.id),
        ])

    def get_family(self):
        family_relations = self.env['res.partner.relation.all'].search([
            ('this_partner_id', '=', self.id)
        ]).filtered(lambda rel: rel.other_partner_id.is_family)
        family_partners = family_relations.mapped('other_partner_id')
        return family_partners

    def get_partners(self):
        partner_relations = self.env['res.partner.relation.all'].search([
            ('this_partner_id', '=', self.id)
        ]).filtered(
            lambda rel: rel.other_partner_id.is_partner_full_member
            or rel.other_partner_id.is_partner_collaborator)
        partner_partners = partner_relations.mapped('other_partner_id')
        return partner_partners

    def action_view_protected_data(self):
        protected_data = self.get_protected_data(self)
        form_view = self.env.ref('healthcare.partner_protected_data_form_view')
        tree_view = self.env.ref('healthcare.partner_protected_data_tree_view')
        action_vals = {
            'name': _('Protected data'),
            'res_model': 'partner.protected.data',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'view_type': 'form',
            'domain': [('id', 'in', protected_data.ids)],
        }
        if len(protected_data) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': protected_data.ids[0],
            })
        return action_vals

    def action_view_info_data(self):
        info_data = self.get_info_data(self)
        form_view = self.env.ref('healthcare.partner_info_data_form_view')
        tree_view = self.env.ref('healthcare.partner_info_data_tree_view')
        action_vals = {
            'name': _('Info data'),
            'res_model': 'partner.info.data',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'view_type': 'form',
            'domain': [('id', 'in', info_data.ids)],
        }
        if len(info_data) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': info_data.ids[0],
            })
        return action_vals

    def action_view_partner_history(self):
        history = self.get_partner_history(self)
        form_view = self.env.ref('healthcare.partner_history_form_view')
        tree_view = self.env.ref('healthcare.partner_history_tree_view')
        search_view = self.env.ref('healthcare.partner_history_search_view')
        action_vals = {
            'name': _('Partner history'),
            'res_model': 'partner.history',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', history.ids)],
            'context': {
                'default_partner_id': self.id,
            },
        }
        if len(history) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': history.ids[0],
            })
        return action_vals

    def action_view_family(self):
        family = self.get_family()
        form_view = self.env.ref('base.view_partner_form')
        tree_view = self.env.ref('base.view_partner_tree')
        search_view = self.env.ref('base.view_res_partner_filter')
        action_vals = {
            'name': _('Family'),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', family.ids)],
            'context': {},
        }
        if len(family) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': family.ids[0],
            })
        return action_vals

    def action_view_partners(self):
        partners = self.get_partners()
        form_view = self.env.ref('base.view_partner_form')
        tree_view = self.env.ref('base.view_partner_tree')
        search_view = self.env.ref('base.view_res_partner_filter')
        action_vals = {
            'name': _('Partners'),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', partners.ids)],
            'context': {},
        }
        if len(partners) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': partners.ids[0],
            })
        return action_vals
