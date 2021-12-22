###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ChapterTemplate(models.Model):
    _name = 'simulation.cost.chapter.template'
    _description = 'Simulation Cost Chapter Template'
    _order = 'display_name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    parent_id = fields.Many2one(
        comodel_name='simulation.cost.chapter.template',
        string='Parent',
    )
    child_ids = fields.One2many(
        comodel_name='simulation.cost.chapter.template',
        inverse_name='parent_id',
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    description = fields.Text(
        string='Description',
    )

    @api.depends('name', 'parent_id')
    def _compute_display_name(self):

        def _get_recursive_name(tmpl):
            if not tmpl.parent_id:
                return tmpl.name
            return '%s/%s' % (_get_recursive_name(tmpl.parent_id), tmpl.name)

        for chapter in self:
            if chapter.name:
                chapter.display_name = _get_recursive_name(chapter)

    @api.multi
    def name_get(self):
        res = []

        def _get_recursive_name(tmpl):
            if not tmpl.parent_id:
                return tmpl.name
            return '%s/%s' % (_get_recursive_name(tmpl.parent_id), tmpl.name)

        for r in self:
            name = _get_recursive_name(r)
            res.append((r.id, name))
        return res

    @api.multi
    def get_parents(self, include_this=False):
        self.ensure_one()
        res = include_this and [self] or []
        if not self.parent_id:
            return res
        return self.parent_id.get_parents(include_this=True) + res

    @api.multi
    def get_childs(self, include_this=False):
        self.ensure_one()
        res = include_this and [self] or []
        if not self.child_ids:
            return res
        for child in self.child_ids:
            res += child.get_childs(include_this=True)
        return res
