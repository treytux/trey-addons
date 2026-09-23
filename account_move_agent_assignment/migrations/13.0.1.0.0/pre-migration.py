###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openupgradelib import openupgrade

_model_renames = [
    ("account.invoice.agent.assignment", "account.move.agent.assignment"),
]

_table_renames = [
    ("account_invoice_agent_assignment", "account_move_agent_assignment"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
