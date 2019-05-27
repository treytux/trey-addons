# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.osv import expression


class ProductTemplateHscode(models.Model):
    _name = 'product.template.hscode'
    _description = 'Product Template HS Code'
    _rec_name = 'code'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'code'
    _order = 'parent_left'

    code = fields.Char(
        string='Code',
        size=64,
        required=True,
        index=True,
        help="HS Code")
    name = fields.Char(
        string='Name',
        index=True,
        required=True,
        translate=True)
    description = fields.Text(
        string='Description',
        required=False,
        translate=True,
        help="HS Name")
    hs_type = fields.Selection(
        selection=[('view', 'View'),
                   ('normal', 'Normal')],
        string='Category Type',
        default='normal',
        help="A category of the view type is a virtual category that can be "
             "used as the parent of another category to create a "
             "hierarchical structure.")
    parent_id = fields.Many2one(
        comodel_name='product.template.hscode',
        string='Parent Category',
        index=True,
        ondelete='cascade')
    child_id = fields.One2many(
        comodel_name='product.category',
        inverse_name='parent_id',
        string='Child Categories')
    parent_left = fields.Integer(
        string='Left Parent',
        index=1)
    parent_right = fields.Integer(
        string='Right Parent',
        index=1)

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(
                _('Error ! You cannot create recursive categories.'))
        return True

    @api.multi
    def code_get(self):
        def get_names(cat):
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def code_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            category_names = name.split(' / ')
            parents = list(category_names)
            child = parents.pop()
            domain = [('name', operator, child)]
            if parents:
                names_ids = self.name_search(
                    ' / '.join(parents), args=args, operator='ilike',
                    limit=limit)
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([('id', 'not in', category_ids)])
                    domain = expression.OR(
                        [[('parent_id', 'in', categories.ids)], domain])
                else:
                    domain = expression.AND(
                        [[('parent_id', 'in', category_ids)], domain])
                for i in range(1, len(category_names)):
                    domain = [[('name', operator,
                                ' / '.join(category_names[-1 - i:]))], domain]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            categories = self.search(
                expression.AND([domain, args]), limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for hscode in self:
            name = hscode.code + ' ' + hscode.name
            result.append((hscode.id, name))
        return result
