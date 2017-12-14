(function () {
    'use strict';
    $(document).ready(function () {
        $('.oe_website_sale').each(function () {
            var oe_website_sale = this;
            $('form.js_features input', oe_website_sale).on('change', function () {
                $(this).closest("form").submit();
            });
        });
    });
})();
