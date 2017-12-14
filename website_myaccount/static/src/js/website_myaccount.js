(function () {
    'use strict';

    var website = openerp.website;
    var _t = openerp._t;

    openerp.website.ready().done(function() {
        website.website_myaccount = {};
        website.website_myaccount.Address = openerp.Widget.extend({
            dom_ready: $.Deferred(),
            ready: function(){
                return this.dom_ready.then(function() {}).promise();
            },
            init: function (parent, options) {
                this.dom_ready.resolve();
                var self = this;
                this._super(parent);

                $('.js_my_address_form').each(function(){
                    var $address = $(this);
                    var country = 'select[name="country_id"]';
                    var country_id = $(this).find('option:selected').val();
                    var state = 'select[name="state_id"]';
                    var $select = $("select[name='state_id']");
                    $address.on('change', country, function () {
                        $select.find('option:not(:first)').attr('disabled', 'disabled').hide();
                        $select.find('option[data-country_id=' + ( $(this).val() || 0 )+ ']').removeAttr('disabled').show();
                    });
                    self.hide_states($select, country_id);
                });
            },
            hide_states: function ($select, country_id) {
                $select.find('option').not('[data-country_id="' + country_id + '"]').attr('disabled', 'disabled').hide();
                $select.find('option').first().removeAttr('disabled').show();
            },
        });

        $('[data-toggle="tooltip"]').tooltip();
        $('.a-submit').each(function(){
            $(this).on('click', function (event) {
                event.preventDefault();
                var $anchor = $(this);
                var $form = $anchor.closest('form');
                var $alert = $form.find('.alert');
                var fields = {};
                $anchor.button('loading');
                $alert.addClass('hidden');
                $alert.removeClass('alert-success');
                $alert.removeClass('alert-danger');
                $form.find('.form-group').removeClass('has-error');
                $form.find('input[type="text"], input[type="password"], select, textarea').each(function() {
                    fields[$(this).attr('name')] = $(this).val();
                });
                $form.find('input[type="radio"]:checked').each(function() {
                    fields[$(this).attr('name')] = $(this).val();
                    console.log(fields[$(this).attr('name')]);
                });

                openerp.jsonRpc($form.attr('action'), 'call', {'fields': fields}).then(function (response) {
                    $anchor.button('reset');
                    if(response.errors.length > 0){
                        var errorsMsg = '';
                        for (var i = 0; i < response.errors.length; i++) {
                            errorsMsg += response.errors[i]['msg'] + '<br/>';
                            $form.find('[name="' + response.errors[i]['field'] + '"]').closest('.form-group').addClass('has-error');
                        }
                        $alert.removeClass('hidden');
                        $alert.html(errorsMsg);
                        $alert.addClass('alert-danger');
                        $alert.fadeIn('fast');
                    } else if(response.result){
                        $alert.removeClass('hidden');
                        $alert.html(_t('Successfully saved.'));
                        $alert.addClass('alert-success');
                        $alert.fadeIn('fast', function () {
                            $(this).delay(2000).fadeOut('fast');
                        });
                    }
                });
            });
        });
        openerp.website.if_dom_contains('select[name="lang"]', function(){
            $('select[name="lang"]').val($('select[name="lang"]').data('value'));
        });
        openerp.website.if_dom_contains('select[name="tz"]', function(){
            $('select[name="tz"]').val($('select[name="tz"]').data('value'));
        });
        openerp.website.if_dom_contains('.js_my_mail_msg_expand', function(){
            $('.js_my_mail_msg_expand a').on('click', function(e){
                e.preventDefault();
                var $self = $(this).parent();
                var $mail_msg = $self.closest('.js_my_mail_msg');
                $self.attr('style', 'display: none;');
                $mail_msg.find('.js_my_mail_msg_body_short').attr('style', 'display: none;');
                $mail_msg.find('.js_my_mail_msg_body_long').attr('style', '');
            });
        });
        openerp.website.if_dom_contains('.js_my_address_form', function(){
            var website_myaccount_address = new website.website_myaccount.Address();
        });
        // openerp.website.if_dom_contains('.js_my_widget_messages', function(){
        //     openerp.jsonRpc('/my/home/get_widget_messages', 'call', {}).then(function (response) {
        //         if(response.to_read){
        //             $('.js_my_widget_messages .o_my_widget_value').html(response.to_read);
        //         }
        //     });
        // });
    });
})();
