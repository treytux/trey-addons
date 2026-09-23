###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class RatingMixin(models.AbstractModel):
    _inherit = 'rating.mixin'

    def rating_apply(self, rate, token=None, feedback=None, subtype=None):
        return super(RatingMixin, self).rating_apply(
            rate, token=token, feedback=feedback, subtype="project.mt_note")
