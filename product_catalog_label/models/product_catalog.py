###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class ProductCatalog(models.Model):
    _name = 'product.catalog'
    _description = 'Product catalog label'

    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    product_count = fields.Integer(
        string='Product count',
        compute='_compute_product_count',
    )
    users_count = fields.Integer(
        string='Users count',
        compute='_compute_users_count',
    )

    def get_users_catalogs(self, catalog):
        return self.env['res.users'].search([
            ('catalog_ids', 'in', catalog.id),
        ])

    @api.multi
    def _compute_users_count(self):
        for record in self:
            record.users_count = len(self.get_users_catalogs(record))

    def get_product_catalogs(self, catalog):
        return self.env['product.template'].search([
            ('catalog_ids', 'in', catalog.id),
        ])

    @api.multi
    def _compute_product_count(self):
        for record in self:
            record.product_count = len(self.get_product_catalogs(record))

    def action_view_users_catalog_link(self):
        users = self.get_users_catalogs(self)
        form_view = self.env.ref('base.view_users_form')
        tree_view = self.env.ref('base.view_users_tree')
        search_view = self.env.ref('base.view_users_search')
        action_vals = {
            'name': _('Users'),
            'res_model': 'res.users',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', users.ids)],
        }
        if len(users) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': users[0].id,
            })
        return action_vals

    def action_view_products_catalog_link(self):
        products = self.get_product_catalogs(self)
        form_view = self.env.ref('product.product_template_form_view')
        tree_view = self.env.ref('product.product_template_tree_view')
        search_view = self.env.ref('product.product_template_search_view')
        action_vals = {
            'name': _('Products'),
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', products.ids)],
        }
        if len(products) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': products[0].id,
            })
        return action_vals
