###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, exceptions, _


class DataQuality(models.Model):
    _name = 'data.quality'
    _description = 'Data Quality'

    name = fields.Char(
        string='Name',
        required=True)
    model_id = fields.Many2one(
        comodel_name='ir.model',
        required=True)
    model_name = fields.Char(
        related='model_id.model')
    max_value = fields.Integer(
        string='Max Value',
        default=100,
        required=True)
    line_ids = fields.One2many(
        comodel_name='data.quality.line',
        inverse_name='quality_id',
        string='Lines',
        required=False)
    line_value = fields.Integer(
        string='Lines Value',
        compute='_compute_line_value',
        required=False)
    domain_force = fields.Text(
        string='Domain')

    @api.one
    @api.constrains('model_id')
    def _check_unique_model_id(self):
        ids = self.search([
            ('id', '!=', self.id), ('model_id', '=', self.model_id.id)])
        if ids:
            raise exceptions.Warning(
                _('Model already exists in another quality rule'))

    @api.one
    @api.depends('line_ids.field_id')
    def _compute_line_value(self):
        self.line_value = sum([l.value for l in self.line_ids])

    @api.model
    def compute_rule(self, record=None):
        rule_id = self.env['data.quality'].search([
            ('model_name', '=', record._name)])
        if not rule_id:
            return 0
        if self.domain_force:
            res = self.env[self.model_id.name].search(self.domain_force)
            if record.id not in res.ids:
                return 0
        rule_value = sum(
            l.compute_line_rule(record=record)[0] for l in rule_id.line_ids)
        return rule_value
