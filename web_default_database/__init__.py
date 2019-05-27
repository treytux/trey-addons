# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import http, tools
import logging
_log = logging.getLogger(__name__)

if tools.config.get('db_defaults', None):
    try:
        tools.config['db_defaults'] = tools.config['db_defaults'].split(',')
        rules = []
        for rule in tools.config['db_defaults']:
            rule = rule.split(':')
            if len(rule) != 2:
                raise ValueError()
            rules.append((rule[0], rule[1]))
        tools.config['db_defaults'] = rules
    except ValueError:
        _log.error('db_defaults option malformed, expected a string '
                   'DOMAIN:DB,DOMAIN:DB,...')
    else:
        def monkey_patch_db_filter(dbs, httprequest=None):
            httprequest = httprequest or http.request.httprequest
            for rule in tools.config['db_defaults']:
                if rule[0] in httprequest.host and rule[1] in dbs:
                    return [rule[1]]
            return []

        def monkey_patch_db_monodb(httprequest=None):
            httprequest = httprequest or http.request.httprequest
            dbs = http.dispatch_rpc("db", "list", [True])
            db_session = httprequest.session.db
            if db_session in dbs:
                return db_session
            for rule in tools.config['db_defaults']:
                if rule[0] in httprequest.host and rule[1] in dbs:
                    return rule[1]
            _log.error('Default database for domain %s not exists!!!' %
                       httprequest.host)
            if len(dbs) == 1:
                return dbs[0]
            return None

        http.db_monodb = monkey_patch_db_monodb
        http.db_filter = monkey_patch_db_filter

else:
    _log.info('Default database not set, add "db_defaults" to config file')
