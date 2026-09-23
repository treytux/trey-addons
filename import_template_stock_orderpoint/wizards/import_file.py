###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

from odoo import _, models
from odoo.exceptions import UserError

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ImportFile(models.TransientModel):
    _inherit = 'import.file'

    def _parse_float(self, value, field):
        self.ensure_one()
        if self.template_id.model_id.model == \
                'import.template.stock_orderpoint':
            value = ''.join([
                v for v in str(value).replace(',', '.')
                if v in '0123456789+-.'])
            return None if value == '' else self._parse_with_cast(float, value)
        return super()._parse_float(value=value, field=field)

    def dataframe_get(self):
        self.ensure_one()
        if self.template_id.model_id.model == \
                'import.template.stock_orderpoint':
            buf = io.BytesIO()
            buf.write(base64.b64decode(self.file))
            ext = self.file_filename.split('.')[-1:][0]
            if ext in ['xls']:
                df = pd.read_excel(
                    buf, encoding='utf-8', engine='xlrd', na_values=['NULL'],
                    converters={'product_id': str})
                return df.where((pd.notnull(df)), False)
            elif ext in ['xlsx']:
                raise UserError(_(
                    'File extension must be \'xls\' for Excel or '
                    '\'csv\' for csv.'))
        return super().dataframe_get()
