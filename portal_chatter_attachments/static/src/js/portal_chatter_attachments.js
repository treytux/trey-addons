odoo.define('portal_chatter_attachments.attachment', function (require) {
'use strict';
	var ajax = require('web.ajax');
	var core = require('web.core');
	var qweb = core.qweb;
	var portalchatter = require('portal.chatter');
	portalchatter.PortalChatter.include({
		events: {
	        'change .o_portal_chatter_file_input': '_onFileInputChange',
	        'click .o_portal_chatter_attachment_btn': '_onAttachmentButtonClick',
	        'click .o_portal_chatter_attachment_delete': '_onAttachmentDeleteClick',
	        'click .o_portal_chatter_composer_btn': '_onSubmitButtonClick',
	    },
		init: function (parent, options) {
	        this._super.apply(this, arguments);
	        this.options = _.defaults(options || {}, {
	            'allow_composer': true,
	            'display_composer': false,
	            'csrf_token': odoo.csrf_token,
	            'token': false,
	            'res_model': false,
	            'res_id': false,
	        });
	        this.attachments = [];
	    },
	    start: function () {
	        var self = this;
	        this.$attachmentButton = this.$('.o_portal_chatter_attachment_btn');
	        this.$fileInput = this.$('.o_portal_chatter_file_input');
	        this.$sendButton = this.$('.o_portal_chatter_composer_btn');
	        this.$attachments = this.$('.o_portal_chatter_composer_form .o_portal_chatter_attachments');
	        this.$attachmentIds = this.$('.o_portal_chatter_attachment_ids');
	        this.$attachmentTokens = this.$('.o_portal_chatter_attachment_tokens');
	        return this._super.apply(this, arguments).then(function () {
	            if (self.options.default_attachment_ids) {
	                self.attachments = self.options.default_attachment_ids || [];
	                _.each(self.attachments, function(attachment) {
	                    attachment.state = 'done';
	                });
	                self._updateAttachments();
	            }
	            return Promise.resolve();
	        });
	    },
	    _loadTemplates: function(){
			return $.when(this._super(), ajax.loadXML('/portal_chatter_attachments/static/src/xml/portal_chatter_attachments.xml', qweb));
		},
	    _onAttachmentButtonClick: function () {
	        this.$fileInput.click();
	    },
	    _onFileInputChange: function () {
	        var self = this;
	        this.$sendButton.prop('disabled', true);
	        return Promise.all(_.map(this.$fileInput[0].files, function (file) {
	            return new Promise(function (resolve, reject) {
	                var data = {
	                    'name': file.name,
	                    'file': file,
	                    'res_id': self.options.res_id,
	                    'res_model': self.options.res_model,
	                    'access_token': self.options.token,
	                };
	                ajax.post('/portal/attachment/add', data).then(function (attachment) {
	                    attachment.state = 'pending';
	                    self.attachments.push(attachment);
	                    self._updateAttachments();
	                    resolve();
	                });
	            });
	        })).then(function () {
	            self.$sendButton.prop('disabled', false);
	        });
	    },
	    _onSubmitButtonClick: function () {
	        return new Promise(function (resolve, reject) {});
	    },
	    _updateAttachments: function () {
	        this.$attachmentIds.val(_.pluck(this.attachments, 'id'));
	        this.$attachmentTokens.val(_.pluck(this.attachments, 'access_token'));
	        this.$attachments.html(qweb.render('portal.Chatter.Attachments', {
	            attachments: this.attachments,
	            showDelete: true,
	        }));
	    },
	});
});
