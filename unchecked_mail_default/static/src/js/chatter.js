odoo.define('unchecked_mail_default.chatter', function (require) {
"use strict";

    var Chatter = require('mail.Chatter');
    var mailUtils = require('mail.utils');

    Chatter.include({
        _onOpenComposerMessage: function () {
            var self = this;
            if (!this.suggested_partners_def) {
                this.suggested_partners_def = $.Deferred();
                var method = 'message_get_suggested_recipients';
                var args = [[this.context.default_res_id], this.context];
                this._rpc({model: this.record.model, method: method, args: args})
                    .then(function (result) {
                        if (!self.suggested_partners_def) {
                            return;
                        }
                        var suggested_partners = [];
                        var thread_recipients = result[self.context.default_res_id];
                        _.each(thread_recipients, function (recipient) {
                            var parsed_email = recipient[1] && mailUtils.parseEmail(recipient[1]);
                            suggested_partners.push({
                                checked: false,
                                partner_id: recipient[0],
                                full_name: recipient[1],
                                name: parsed_email[0],
                                email_address: parsed_email[1],
                                reason: recipient[2],
                            });
                        });
                        self.suggested_partners_def.resolve(suggested_partners);
                    });
            }
            this.suggested_partners_def.then(function (suggested_partners) {
                self._openComposer({ isLog: false, suggested_partners: suggested_partners });
            });
        }
    });
});
