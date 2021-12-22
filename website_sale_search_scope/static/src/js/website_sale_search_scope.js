odoo.define('website_sale_search_scope.scope_selector', function (require) {
    "use strict";
    require('web.dom_ready');
    let $buttons = $('.js_ss_category_btn');
    if($buttons.length) {
        $buttons.on('click', function(e){
            e.preventDefault();
            let $current = $('.js_ss_current_category');
            let $form = $(this).closest('form');
            $current.text($(this).text());
            $form.attr('action', $(this).data('action'));
        });
    }
});
