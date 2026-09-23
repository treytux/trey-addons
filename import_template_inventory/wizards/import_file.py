###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

from odoo import models

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ImportFile(models.TransientModel):
    _inherit = 'import.file'

    def _parse_float(self, value, field):
        self.ensure_one()
        if self.template_id.model_id.model == 'import.template.inventory':
            value = ''.join([
                v for v in str(value).replace(',', '.')
                if v in '0123456789+-.'])
            return None if value == '' else self._parse_with_cast(float, value)
        return super()._parse_float(value=value, field=field)

    def dataframe_get(self):
        self.ensure_one()
        if self.template_id.model_id.model == 'import.template.inventory':
            buf = io.BytesIO()
            buf.write(base64.b64decode(self.file))
            ext = self.file_filename.split('.')[-1:][0]
            if ext in ['xlsx', 'xls']:
                df = pd.read_excel(
                    buf, engine='xlrd', encoding='utf-8', na_values=['NULL'],
                    converters={'prod_lot_id': str})
                return df.where((pd.notnull(df)), None)
        return super().dataframe_get()
