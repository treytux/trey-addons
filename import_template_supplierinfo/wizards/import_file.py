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

    def dataframe_get(self):
        self.ensure_one()
        if self.template_id.model_id.model == 'import.template.supplierinfo':
            buf = io.BytesIO()
            buf.write(base64.b64decode(self.file))
            ext = self.file_filename.split('.')[-1:][0]
            if ext in ['xlsx', 'xls']:
                df = pd.read_excel(
                    buf, engine='xlrd', encoding='utf-8', na_values=['NULL'],
                    converters={'name': str})
                return df.where((pd.notnull(df)), None)
        return super().dataframe_get()
