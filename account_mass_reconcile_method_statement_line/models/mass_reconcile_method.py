###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMassReconcileMethod(models.Model):
    _inherit = 'account.mass.reconcile.method'

    sql_filter = fields.Char(
        string='Filter',
    )

    def _selection_name(self):
        values = super()._selection_name()
        values.append((
            'mass.reconcile.statement.line',
            'Statement line. Set account by filter name'
        ))
        return values
