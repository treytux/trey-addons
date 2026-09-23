###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountMassReconcile(models.Model):
    _inherit = 'account.mass.reconcile'

    def _run_reconcile_method(self, reconcile_method):
        if reconcile_method.name != 'mass.reconcile.statement.line':
            return super()._run_reconcile_method(reconcile_method)
        rec_model = self.env[reconcile_method.name]
        vals = self._prepare_run_transient(reconcile_method)
        vals['_filter'] = reconcile_method.sql_filter
        method = rec_model.create(vals)
        return method.action_reconcile(reconcile_method)
