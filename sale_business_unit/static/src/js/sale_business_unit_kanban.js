odoo.define('sale_business_unit.business_unit_dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var KanbanRecord = require('web.KanbanRecord');
    var _t = core._t;

    KanbanRecord.include({
        events: _.defaults({
            'click .business_unit_target_definition': '_onBusinessUnitTargetClick',
        }, KanbanRecord.prototype.events),
        _onBusinessUnitTargetClick: function (ev) {
            ev.preventDefault();
            var self = this;
            this.$target_input = $('<input>');
            this.$('.o_kanban_primary_bottom:last').html(this.$target_input);
            this.$('.o_kanban_primary_bottom:last').prepend(_t("Set an invoicing target: "));
            this.$target_input.focus();
            this.$target_input.on({
                blur: this._onBusinessUnitTargetSet.bind(this),
                keydown: function (ev) {
                    if (ev.keyCode === $.ui.keyCode.ENTER) {
                        self._onBusinessUnitTargetSet();
                    }
                },
            });
        },
        _onBusinessUnitTargetSet: function () {
            var self = this;
            var value = Number(this.$target_input.val());
            if (isNaN(value)) {
                this.do_warn(_t("Wrong value entered!"), _t("Only Integer Value should be valid."));
            } else {
                this.trigger_up('kanban_record_update', {invoiced_target: value});
                this.trigger_up('reload');
            }
        },
    });
});
