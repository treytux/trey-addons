###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class WizProductLabelGondola(models.TransientModel):
    _name = 'wizard.product.label.gondola'
    _description = 'Wizard for report label by gondola shelving'

    quantity_label = fields.Integer(
        string='Quantity',
        help='Set the quantity of labels per product',
        default=1,
    )

    def _get_default_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search(
                [('name', 'ilike', '(product_label_gondola)')])
        if not reports.exists():
            return None
        return reports[0]

    @api.model
    def _get_domain_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search(
                [('name', 'ilike', '(product_label_gondola)')])
        return [('id', 'in', reports and reports.ids or [0])]

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Report',
        domain=_get_domain_report,
        default=_get_default_report,
        required=True,
    )

    def _prepare_report_data(self):
        self.ensure_one()
        data = {
            'model': 'product.product',
            'quantity': self.quantity_label,
            'product_ids': self.env.context.get('active_ids', []),
        }
        return data

    def button_print(self):
        self.ensure_one()
        datas = self._prepare_report_data()
        return self.env.ref(
            self.report_id.xml_id).report_action(self, data=datas)
