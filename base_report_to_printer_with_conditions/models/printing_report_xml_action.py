###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval


class PrintingReportXmlAction(models.Model):
    _inherit = 'printing.report.xml.action'
    _order = 'sequence'

    sequence = fields.Integer(
        index=True,
        default=9999)
    user_id = fields.Many2one(
        required=False)
    python_condition = fields.Char(
        string='Python condition',
        default='True')

    @api.multi
    def pass_condition(self, records):
        self.ensure_one()
        if not self.python_condition:
            return True
        for record in records:
            if not bool(safe_eval(self.python_condition, {'object': record})):
                return False
        return True
