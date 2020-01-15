# Copyright 2019 Vicent Cubells - Trey <http://www.trey.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    default_supplierinfo_multiple_discount = fields.Char(
        string='Default Supplier Multiple Disc. (%)',
        help="This value will be used as the default one, for each new "
             "supplierinfo line depending on that supplier.",
    )
