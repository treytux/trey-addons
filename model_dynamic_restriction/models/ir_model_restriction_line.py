###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class IrModelRestrinctionLine(models.Model):
    _name = 'ir.model.restriction.line'
    _description = 'Model dynamic restriction line'

    restriction_id = fields.Many2one(
        comodel_name='ir.model.restriction',
        string='Restriction',
        ondelete='cascade',
        required=True,
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        related='restriction_id.model_id',
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Field',
        required=True,
    )
    condition = fields.Selection(
        selection=[
            ('required', 'Required'),
            ('number_str_min', 'Min characters'),
            ('number_str_max', 'Max characters'),
            ('number_min', 'Min number'),
            ('number_max', 'Max number'),
            ('str_formula', 'Formula'),
        ],
        string='Condition',
        required=True,
        default='required',
    )
    value_visible = fields.Char(
        string='Value visible',
        compute='_compute_value',
    )
    value_display = fields.Text(
        string='Display value',
        compute='_compute_value',
    )
    value_number = fields.Integer(
        string='Number value',
    )
    value_str = fields.Text(
        string='Str value',
    )
    user_error_message = fields.Char(
        string='User error message',
    )
    when = fields.Selection(
        selection=[
            ('before', 'Before'),
            ('after', 'After'),
        ],
        string='When',
        default='before',
        required=True,
    )

    @api.depends('condition', 'value_number', 'value_str')
    def _compute_value(self):
        for line in self:
            line.value_visible = False
            line.value_display = False
            if not line.condition:
                continue
            fname = 'value_%s' % line.condition.split('_')[0]
            if not hasattr(line, fname):
                continue
            line.value_visible = fname
            txt = getattr(line, fname)
            if len(str(txt or '')) > 255:
                txt = '%x...' % txt[:255]
            line.value_display = txt

    def before_check(self, action, record, vals):
        for line in self.filtered(lambda l: l.when == 'before'):
            line._check(action, record, vals)

    def after_check(self, action, record, vals):
        for line in self.filtered(lambda l: l.when == 'after'):
            line._check(action, record, vals)

    def _check(self, action, record, vals):
        def parse_error(line, message, value):
            return _('· Field "%s": %s (value "%s"). %s') % (
                line.field_id.field_description, message, value,
                line.user_error_message)

        errors = []
        for line in self:
            fnc = getattr(line, 'check_%s' % line.condition)
            fname = self.field_id.name
            value = vals[fname] if fname in vals else record[fname]
            ok, message = fnc(action, record, vals, value)
            if not ok:
                errors.append(parse_error(line, message, value))
        if errors:
            msg = _(
                'The model "%s" (%s) raise exceptions on %s '
                'action by dynamic restriction "%s":\n%s' % (
                    line.restriction_id.model_id.name,
                    line.restriction_id.model_id.model,
                    action, line.restriction_id.name, '\n'.join(errors)))
            raise ValidationError(msg)

    def check_required(self, action, record, vals, value):
        self.ensure_one()
        msg = _('Value is required')
        if not value:
            return (False, msg)
        return (True, msg)

    def check_number_str_min(self, action, record, vals, value):
        self.ensure_one()
        msg = _('Min %s characters') % self.value_number
        value = str(value or '')
        if len(value) < self.value_number:
            return (False, msg)
        return (True, msg)

    def check_number_str_max(self, action, record, vals, value):
        self.ensure_one()
        msg = _('Max %s characters') % self.value_number
        value = str(value or '')
        if len(value) > self.value_number:
            return (False, msg)
        return (True, msg)

    def check_number_min(self, action, record, vals, value):
        self.ensure_one()
        msg = _('Min number allowed is %s') % self.value_number
        value = value or 0
        if value < self.value_number:
            return (False, msg)
        return (True, msg)

    def check_number_max(self, action, record, vals, value):
        self.ensure_one()
        msg = _('Max number allowed is %s') % self.value_number
        value = value or 0
        if value > self.value_number:
            return (False, msg)
        return (True, msg)

    def check_str_formula(self, action, record, vals, value):
        self.ensure_one()
        msg = _('It does not pass the criteria of the formula.')
        results = {
            'result': False,
            'self': self,
            'action': action,
            'record': record,
            'vals': vals,
            'value': value,
        }
        safe_eval(self.value_str, results, mode='exec', nocopy=True)
        if not results['result']:
            return (False, msg)
        return (True, msg)
