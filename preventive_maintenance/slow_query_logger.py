###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import hashlib
import logging
import os
import re
import socket
import threading
import time
from contextvars import ContextVar
from datetime import datetime

from odoo import sql_db
from odoo.tools import config
from psycopg2.extras import execute_values

_logger = logging.getLogger(__name__)
_guard = ContextVar('preventive_slow_query_guard', default=False)
_space = re.compile(r'\s+')
_table = 'preventive_maintenance_slow_query_history'
_overflow_id = '__overflow__'


def _integer_setting(name, default):
    config_name = name.removeprefix('ODOO_').lower()
    value = os.environ.get(name, config.get(config_name, str(default)))
    try:
        return int(value)
    except (TypeError, ValueError):
        _logger.warning('Invalid %s value; using %s.', name, default)
        return default


SLOW_QUERY_MIN_DURATION_MS = _integer_setting(
    'ODOO_PREVENTIVE_SLOW_QUERY_MIN_DURATION_MS', -1)
MAX_BUCKETS = _integer_setting('ODOO_PREVENTIVE_SLOW_QUERY_MAX_BUCKETS', 500)
MAX_EVENTS_PER_MINUTE = _integer_setting(
    'ODOO_PREVENTIVE_SLOW_QUERY_MAX_EVENTS_PER_MINUTE', 100)
FLUSH_INTERVAL_SECONDS = _integer_setting(
    'ODOO_PREVENTIVE_SLOW_QUERY_FLUSH_INTERVAL_SECONDS', 60)
MAX_BUCKETS = max(1, MAX_BUCKETS)
MAX_EVENTS_PER_MINUTE = max(1, MAX_EVENTS_PER_MINUTE)
FLUSH_INTERVAL_SECONDS = max(1, FLUSH_INTERVAL_SECONDS)


class SlowQueryBuffer:

    def __init__(self):
        self._lock = threading.Lock()
        self._buckets = {}
        self._events = {}
        self._window_started = {}
        self._last_flush = time.monotonic()
        self._server_name = socket.gethostname()

    def record(self, dbname, query, duration_ms):
        now = datetime.utcnow()
        bucket_start = now.replace(minute=0, second=0, microsecond=0)
        query_id = self._query_id(query)
        key = (dbname, query_id, bucket_start, self._server_name)
        with self._lock:
            if not self._accept_event(dbname, now):
                self._record_overflow(dbname, bucket_start, now)
                return
            database_bucket_count = sum(
                1 for bucket_key in self._buckets if bucket_key[0] == dbname)
            if (
                key not in self._buckets
                    and database_bucket_count >= MAX_BUCKETS):
                self._record_overflow(dbname, bucket_start, now)
                return
            bucket = self._buckets.setdefault(key, self._bucket(now, False))
            bucket['occurrence_count'] += 1
            bucket['total_duration_ms'] += duration_ms
            bucket['min_duration_ms'] = min(
                bucket['min_duration_ms'], duration_ms)
            bucket['max_duration_ms'] = max(
                bucket['max_duration_ms'], duration_ms)
            bucket['date_last'] = now

    def schedule_flush(self, cursor):
        if self._should_flush():
            self.flush()
            return
        if not getattr(
                cursor, '_preventive_slow_query_flush_scheduled', False):
            cursor._preventive_slow_query_flush_scheduled = True
            cursor.postcommit.add(self.flush)

    def flush(self):
        with self._lock:
            if not self._buckets:
                return
            buckets, self._buckets = self._buckets, {}
            self._last_flush = time.monotonic()
        failed = {}
        token = _guard.set(True)
        try:
            for dbname, rows in self._by_database(buckets).items():
                try:
                    self._flush_database(dbname, rows)
                except Exception:
                    failed.update(rows)
                    _logger.exception(
                        'Could not persist preventive slow-query telemetry for'
                        ' database %s.', dbname)
        finally:
            _guard.reset(token)
        if failed:
            with self._lock:
                self._merge(failed)

    def _flush_database(self, dbname, rows):
        with sql_db.db_connect(dbname).cursor() as cr:
            cr.execute("SELECT to_regclass('public.%s')" % _table)
            if not cr.fetchone()[0]:
                raise RuntimeError('preventive_maintenance is not installed')
            values_list = [
                (
                    query_id, bucket_start, values['date_first'],
                    values['date_last'], values['occurrence_count'],
                    values['total_duration_ms'], values['min_duration_ms'],
                    values['max_duration_ms'], values['is_overflow'],
                    server_name)
                for (query_id, bucket_start, server_name), values
                in rows.items()]
            execute_values(cr, '''
                    INSERT INTO preventive_maintenance_slow_query_history
                        (query_id, bucket_start, date_first, date_last,
                         occurrence_count, total_duration_ms, min_duration_ms,
                         max_duration_ms, is_overflow, server_name,
                         create_uid, create_date, write_uid, write_date)
                    VALUES %s
                    ON CONFLICT (query_id, bucket_start, server_name)
                    DO UPDATE SET
                        date_first = LEAST(
                            preventive_maintenance_slow_query_history.
                            date_first,
                            EXCLUDED.date_first),
                        date_last = GREATEST(
                            preventive_maintenance_slow_query_history.
                            date_last,
                            EXCLUDED.date_last),
                        occurrence_count =
                            preventive_maintenance_slow_query_history.
                            occurrence_count +
                            EXCLUDED.occurrence_count,
                        total_duration_ms =
                            preventive_maintenance_slow_query_history.
                            total_duration_ms +
                            EXCLUDED.total_duration_ms,
                        min_duration_ms = LEAST(
                            preventive_maintenance_slow_query_history.
                            min_duration_ms,
                            EXCLUDED.min_duration_ms),
                        max_duration_ms = GREATEST(
                            preventive_maintenance_slow_query_history.
                            max_duration_ms,
                            EXCLUDED.max_duration_ms),
                        write_uid = 1,
                        write_date = NOW() AT TIME ZONE 'UTC'
                ''', values_list, template='''(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    1, NOW() AT TIME ZONE 'UTC',
                    1,NOW() AT TIME ZONE 'UTC')''')

    def _accept_event(self, dbname, now):
        started = self._window_started.get(dbname)
        if started is None or (now - started).total_seconds() >= 60:
            self._window_started[dbname] = now
            self._events[dbname] = 0
        self._events[dbname] += 1
        return self._events[dbname] <= MAX_EVENTS_PER_MINUTE

    def _record_overflow(self, dbname, bucket_start, now):
        key = (dbname, _overflow_id, bucket_start, self._server_name)
        bucket = self._buckets.setdefault(key, self._bucket(now, True))
        bucket['occurrence_count'] += 1
        bucket['date_last'] = now

    def _should_flush(self):
        return time.monotonic() - self._last_flush >= FLUSH_INTERVAL_SECONDS

    @staticmethod
    def _bucket(now, is_overflow):
        return {
            'date_first': now,
            'date_last': now,
            'occurrence_count': 0,
            'total_duration_ms': 0.0,
            'min_duration_ms': 0.0 if is_overflow else float('inf'),
            'max_duration_ms': 0.0,
            'is_overflow': is_overflow,
        }

    @staticmethod
    def _query_id(query):
        query = query.decode(
            'utf-8', 'replace') if isinstance(query, bytes) else str(query)
        normalized = _space.sub(' ', query).strip()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def _by_database(buckets):
        result = {}
        for ((dbname, query_id, bucket_start, server_name),
                values) in buckets.items():
            result.setdefault(dbname, {})[
                (query_id, bucket_start, server_name)] = values
        return result

    def _merge(self, buckets):
        for key, values in buckets.items():
            current = self._buckets.get(key)
            if current is None:
                self._buckets[key] = values
                continue
            current['date_first'] = min(
                current['date_first'], values['date_first'])
            current['date_last'] = max(
                current['date_last'], values['date_last'])
            current['occurrence_count'] += values['occurrence_count']
            current['total_duration_ms'] += values['total_duration_ms']
            current['min_duration_ms'] = min(
                current['min_duration_ms'], values['min_duration_ms'])
            current['max_duration_ms'] = max(
                current['max_duration_ms'], values['max_duration_ms'])


_buffer = SlowQueryBuffer()


def flush_pending():
    _buffer.flush()


if not getattr(sql_db.Cursor, '_preventive_slow_query_cursor', False):
    _Cursor = sql_db.Cursor

    class SlowQueryCursor(_Cursor):
        _preventive_slow_query_cursor = True

        def execute(self, query, params=None, log_exceptions=True):
            if SLOW_QUERY_MIN_DURATION_MS < 0 or _guard.get():
                return super().execute(query, params, log_exceptions)
            start = time.perf_counter()
            result = super().execute(query, params, log_exceptions)
            duration_ms = (time.perf_counter() - start) * 1000.0
            if duration_ms >= SLOW_QUERY_MIN_DURATION_MS:
                _buffer.record(self.dbname, query, duration_ms)
                _buffer.schedule_flush(self)
            return result

    sql_db.Cursor = SlowQueryCursor
