###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info('Starting migration from website.woo.log to ir.model.log')
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'website_woo_log'
        );
    """)
    table_exists = cr.fetchone()[0]
    if not table_exists:
        _logger.info(
            'Table website_woo_log does not exist, nothing to migrate')
        return
    cr.execute("SELECT COUNT(*) FROM website_woo_log")
    count = cr.fetchone()[0]
    if count == 0:
        _logger.info('No records in website_woo_log to migrate')
        return
    cr.execute("""
        INSERT INTO ir_model_log (
            name,
            date_start,
            date_finish,
            elapsed,
            description,
            res_model,
            res_ids,
            website_id,
            create_uid,
            create_date,
            write_uid,
            write_date
        )
        SELECT
            name,
            date_start,
            date_finish,
            elapsed,
            description,
            res_model,
            res_ids,
            website_id,
            create_uid,
            create_date,
            write_uid,
            write_date
        FROM website_woo_log
        WHERE id NOT IN (
            SELECT id FROM ir_model_log WHERE website_id IS NOT NULL
        )
    """)
    migrated = cr.rowcount
    _logger.info(
        f'Migration completed: {migrated} records migrated from '
        'website_woo_log to ir.model.log')
    cr.execute("""
        UPDATE mail_followers
        SET res_model = 'ir.model.log'
        WHERE res_model = 'website.woo.log'
        AND EXISTS (
            SELECT 1 FROM ir_model_log
            WHERE id = mail_followers.res_id
        )
    """)
    cr.execute("""
        UPDATE mail_message
        SET model = 'ir.model.log'
        WHERE model = 'website.woo.log'
        AND EXISTS (
            SELECT 1 FROM ir_model_log
            WHERE id = mail_message.res_id
        )
    """)
    cr.execute("""
        UPDATE mail_activity
        SET res_model = 'ir.model.log',
            res_model_id = (
                SELECT id FROM ir_model WHERE model = 'ir.model.log'
            )
        WHERE res_model = 'website.woo.log'
        AND EXISTS (
            SELECT 1 FROM ir_model_log
            WHERE id = mail_activity.res_id
        )
    """)
    cr.execute("""
        UPDATE ir_attachment
        SET res_model = 'ir.model.log'
        WHERE res_model = 'website.woo.log'
        AND EXISTS (
            SELECT 1 FROM ir_model_log
            WHERE id = ir_attachment.res_id
        )
    """)
    _logger.info(
        'Related data migration completed '
        '(followers, messages, activities, attachments)')
