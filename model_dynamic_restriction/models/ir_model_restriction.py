###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models, api


class IrModelRestrinction(models.Model):
    _name = 'ir.model.restriction'
    _description = 'Model dynamic restriction'

    name = fields.Char(
        string='Name',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        ondelete='set null',
        default=lambda self: self.env.user.company_id.id,
    )
    domain = fields.Char(
        string='Domain',
        help=(
            'Only applicable after create, before and after write, and before '
            'unlink'),
    )
    line_ids = fields.One2many(
        comodel_name='ir.model.restriction.line',
        inverse_name='restriction_id',
        string='Lines',
    )
    group_ids = fields.Many2many(
        comodel_name='res.groups',
        relation='ir_model_restriction2res_groups_rel',
        column1='restriction_id',
        column2='group_ids',
    )
    to_create = fields.Boolean(
        string='Create',
        default=True,
    )
    to_write = fields.Boolean(
        string='Write',
        default=True,
    )
    to_unlink = fields.Boolean(
        string='Unlink',
    )

    def _register_hook(self):
        self.search([]).subscribe()
        return super()._register_hook()

    def apply_domain(self, records):
        self.ensure_one()
        if not self.domain:
            return records
        return records.search(
            [('id', 'in', records.ids)] + eval(self.domain))

    def check_user_groups(self):
        self.ensure_one()
        if not self.group_ids:
            return True
        groups = self.group_ids.filtered(lambda g: self.env.user in g.users)
        return groups.exists() or False

    def subscribe(self):
        def check_company(vals, record=None):
            if not self.company_id:
                return True
            values = isinstance(vals, list) and vals[0] or vals
            if values.get('company_id') == self.company_id.id:
                return True
            if record and 'company_id' in record:
                if record.company_id == self.company_id:
                    return True
            if self.env.user.company_id == self.company_id:
                return True
            return False

        def create(this, vals):
            if not check_company(vals):
                return create.origin(this, vals)
            if not self.check_user_groups():
                return create.origin(this, vals)
            self.line_ids.before_check('create', this, vals)
            res = create.origin(this, vals)
            this_filtered = self.apply_domain(res)
            self.line_ids.after_check('create', this_filtered, vals)
            return res

        def write(this, vals):
            if not check_company(vals, this):
                return write.origin(this, vals)
            if not self.check_user_groups():
                return write.origin(this, vals)
            this_filtered = self.apply_domain(this)
            self.line_ids.before_check('write', this_filtered, vals)
            res = write.origin(this, vals)
            this_filtered = self.apply_domain(this)
            self.line_ids.after_check('write', this_filtered, vals)
            return res

        def unlink(this):
            if not check_company({}):
                return unlink.origin(this)
            if not self.check_user_groups():
                return unlink.origin(this)
            this_filtered = self.apply_domain(this)
            self.line_ids._check('unlink', this_filtered, {})
            return unlink.origin(this)

        for rule in self:
            model = self.env[rule.model_id.model]
            if rule.to_create and not rule.model_id.is_restriction_create:
                model._patch_method('create', create)
            if rule.to_write and not rule.model_id.is_restriction_write:
                model._patch_method('write', write)
            if rule.to_unlink and not rule.model_id.is_restriction_unlink:
                model._patch_method('unlink', unlink)
            rule.model_id.write({
                'is_restriction_create': rule.to_create,
                'is_restriction_write': rule.to_write,
                'is_restriction_unlink': rule.to_unlink,
            })

    def unsubscribe(self):
        def revert(model, method):
            if hasattr(getattr(model, method), 'origin'):
                model._revert_method(method)

        for rule in self:
            model = self.env[rule.model_id.model]
            if rule.model_id.is_restriction_create:
                revert(model, 'create')
            if rule.model_id.is_restriction_write:
                revert(model, 'write')
            if rule.model_id.is_restriction_unlink:
                revert(model, 'unlink')
            rule.model_id.write({
                'is_restriction_create': False,
                'is_restriction_write': False,
                'is_restriction_unlink': False,
            })

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.subscribe()
        return res

    def write(self, vals):
        self.unsubscribe()
        res = super().write(vals)
        self.subscribe()
        return res

    def unlink(self):
        self.unsubscribe()
        return super().unlink()
