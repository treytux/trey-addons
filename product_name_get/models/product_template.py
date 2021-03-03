###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import re

from openerp import api, models

_log = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _name_get_parse(self, pattern, record):
        def _get_field_value(obj, parts):
            value = obj[parts[0]]
            if not parts[1:]:
                return value
            return _get_field_value(value, parts[1:])

        data = {}
        for field in re.findall(r'\((.*?)\)', pattern):
            try:
                data[field] = _get_field_value(record, field.split('.'))
            except Exception:
                _log.error('Field %s in pattern "%s" not exists for %s' % (
                    field, pattern, record._name))
                data[field] = '%%(%s)s' % field
        return pattern % data

    @api.multi
    def name_get(self):
        pattern = self.env['ir.config_parameter'].sudo().get_param(
            'product_name_get.product_template_name_pattern')
        if not pattern or 'partner_id' in self._context:
            return super().name_get()
        return [(p.id, p._name_get_parse(pattern, p)) for p in self]
