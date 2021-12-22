###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_setup = fields.Boolean(
        string='Is setup',
    )
    setup_ids = fields.One2many(
        comodel_name='product.setup.line',
        inverse_name='product_tmpl_id',
        string='Setup lines',
    )
    setup_product_ids = fields.Many2many(
        comodel_name='product.product',
        compute='_compute_setup_product_ids',
    )
    setup_product_count = fields.Integer(
        string='Setup products',
        compute='_compute_setup_product_ids',
    )
    setup_categ_id = fields.Many2one(
        comodel_name='product.setup.category',
        string='Setup category',
    )
    setup_group_id = fields.Many2one(
        comodel_name='product.setup.group',
        string='Setup group',
    )
    setup_property_ids = fields.Many2many(
        string='Properties',
        comodel_name='product.setup.property',
        relation='product_template2setup_property_rel',
        column1='product_tmpl_id',
        column2='property_id',
    )
    setup_property_incompatible_ids = fields.Many2many(
        string='Incompatible',
        comodel_name='product.setup.property',
        relation='product_template2setup_property_incompatible_rel',
        column1='product_tmpl_id',
        column2='property_id',
    )
    setup_group_property_ids = fields.Many2many(
        string='Group properties',
        comodel_name='product.setup.property',
        related='setup_group_id.setup_property_ids',
    )
    setup_group_property_incompatible_ids = fields.Many2many(
        string='Group incompatible',
        comodel_name='product.setup.property',
        related='setup_group_id.setup_property_incompatible_ids',
    )
    setup_categ_ids = fields.One2many(
        comodel_name='product.setup.category',
        inverse_name='product_tmpl_id',
        string='Setup categories',
        compute='_compute_setup_categ_ids',
    )

    def check_setup_categ_id(self):
        for tmpl in self:
            categs = tmpl.setup_property_ids.mapped('categ_id')
            if len(categs) > 1:
                raise exceptions.UserError(_(
                    'A product can only have properties of one category, and '
                    'the product "%s" has more than one') % tmpl.name)

    @api.depends('setup_ids')
    def _compute_setup_product_ids(self):
        for tmpl in self:
            if not tmpl.is_setup:
                continue
            tmpl.setup_product_ids = tmpl.setup_ids.mapped(
                'categ_id.product_tmpl_ids.product_variant_ids')
            tmpl.setup_product_count = len(tmpl.setup_product_ids)

    @api.depends('setup_ids')
    def _compute_setup_categ_ids(self):
        for tmpl in self:
            tmpl.setup_categ_ids = tmpl.setup_ids.mapped('categ_id')

    def action_component_view(self):
        if not self.setup_product_ids:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env.ref('product.product_normal_action').read()[0]
        action['domain'] = [('id', 'in', self.setup_product_ids.ids)]
        return action
