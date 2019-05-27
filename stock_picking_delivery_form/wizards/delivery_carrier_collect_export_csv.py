# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class DeliveryCarrierCollectExportCsv(models.TransientModel):
    _name = 'delivery.carrier.collect_export_csv'

    file = fields.Binary(
        string='File',
        readonly=True,
        filter='*.csv')
    file_name = fields.Char(
        string='File name',
        default='carrier.csv',
        readonly=True)
