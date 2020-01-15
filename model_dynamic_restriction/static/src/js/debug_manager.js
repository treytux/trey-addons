odoo.define('model_dynamic_restriction.DebugManager', function (require) {
    'use strict';

    var DebugManager = require('web.DebugManager');
    var core = require('web.core');
    var _t = core._t;

    DebugManager.include({
        dynamic_restriction: function () {
            var model = this._action.res_model,
                self = this;
            console.log(model)
            console.log(model)
            console.log(model)
            this._rpc({
                model: 'ir.model',
                method: 'search',
                args: [[['model', '=', model]]]
            }).done(function (ids) {
                self.do_action({
                    res_model: 'ir.model.restriction',
                    name: _t('Dynamic restriction'),
                    views: [[false, 'list'], [false, 'form']],
                    domain: [['model_id.model', '=', model]],
                    type: 'ir.actions.act_window',
                    context: {
                        'default_model_id': ids[0]
                    }
                });
            });
        }
    });
});
