/*
# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
*/

var INSTANCE = null;

openerp.web_disable_export_by_group = function(instance) {
    INSTANCE = instance;
    var _t = instance.web._t;
    var SUPERUSER_ID = 1;
    var ALLOW_USER = false;

    instance.session.rpc('/web/export/user_allowed', {
        model: 'res.users'
    }).done(function(user_allowed) {
        ALLOW_USER = user_allowed;
    });

    instance.web.Sidebar.include({
        add_items: function(section_code, items) {
            if ((this.session.uid == SUPERUSER_ID) || (ALLOW_USER)) {
                this._super.apply(this, arguments);
            }
            else {
                var export_label = _t("Export");
                var new_items = items;
                if (section_code == 'other') {
                    new_items = [];
                    for (var i = 0; i < items.length; i++) {
                        if (items[i]['label'] != export_label) {
                            new_items.push(items[i]);
                        };
                    };
                };
                if (new_items.length > 0) {
                    this._super.call(this, section_code, new_items);
                };
            }
        }
    });
};
