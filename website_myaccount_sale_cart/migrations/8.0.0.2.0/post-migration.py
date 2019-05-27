# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import pooler, SUPERUSER_ID


def migrate_payment_types(pool, cr, uid):
    model = pool.get('ir.model.data')
    section_id = model.get_object(
        cr, uid, 'website', 'salesteam_website_sales').id
    cr.execute("""
        UPDATE sale_order
        SET website_order=True
        WHERE section_id=%s
        """ % section_id)


def migrate(cr, version):
    pool = pooler.get_pool(cr.dbname)
    migrate_payment_types(pool, cr, SUPERUSER_ID)
