###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, exceptions, _


class DataQualityLine(models.Model):
    _name = 'data.quality.line'
    _description = 'Data Quality Line'

    quality_id = fields.Many2one(
        comodel_name='data.quality',
        string='Quality',
        ondelete='cascade',
        required=True)
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Field',
        required=True)
    field_name = fields.Char(
        related='field_id.name')
    value_character = fields.Integer(
        string='Characters',
        default='30',
        required=True)
    value = fields.Integer(
        string='Value',
        default=10,
        required=True)
    domain_force = fields.Text(
        string='Domain')

    @api.one
    @api.constrains('field_id')
    def _check_unique_field_id(self):
        ids = self.search([
            ('id', '!=', self.id), ('field_id', '=', self.field_id.id)])
        if ids:
            raise exceptions.Warning(_('Field already exists with this lines'))

    @api.one
    def compute_line_rule(self, record):
        value = record[self.field_name]
        if not value:
            return 0
        if not hasattr(self, 'parse_%s' % self.field_id.ttype):
            return 0
        fnc = getattr(self, 'parse_%s' % self.field_id.ttype)
        return fnc(record, value)

    @api.multi
    def parse_char(self, record, value):
        value = value.replace(' ', '')
        if len(value) >= self.value_character:
            return self.value
        if len(value) == 0 or None:
            return 0
        return (len(value) * self.value) / self.value_character or 0

    @api.multi
    def parse_text(self, record, value):
        value = value.replace('\n', '').replace('\r', '')
        return self.parse_char(record, value)

    @api.multi
    def parse_html(self, record, value):
        return self.parse_txt(record, value)
