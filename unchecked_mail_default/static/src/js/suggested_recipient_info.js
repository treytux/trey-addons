odoo.define('unchecked_mail_default.SuggestedRecipientInfo', function (require) {
    const { registry } = require('@mail/model/model_core');
    const { attr } =  require('@mail/model/model_field');
    registry.get('SuggestedRecipientInfo').get('fields').get('isSelected').default = false;
})
