###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockQuantPackageDummyType(models.Model):
    _name = 'stock.quant_package.dummy.type'
    _description = 'Stock quant package dummy type'

    def _get_default_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(dummy_label)')])
        if not reports.exists():
            return None
        return reports[0]

    def _get_domain_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(dummy_label)')])
        return [('id', 'in', reports and reports.ids or [0])]

    name = fields.Char(
        string='Name',
    )
    prefix = fields.Char(
        string='Prefix',
    )
    dummy_type = fields.Selection(
        selection=[
            ('dummy', 'Dummy'),
            ('mixed_package', 'Mixed package'),
            ('pallet', 'Pallet'),
        ],
    )
    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Report',
        domain=_get_domain_report,
        default=_get_default_report,
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )

    @api.constrains('dummy_type')
    def _check_duplicated_dummy_types(self):
        for record in self:
            count = self.search_count([
                ('dummy_type', '=', record.dummy_type),
            ])
            if count > 1:
                raise ValidationError(_(
                    'There is already a record with this selection'
                    ' in the company'))
