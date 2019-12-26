odoo.define('website_snippet_instagram_feed.snippets', function (require) {
    'use strict';

    require('web.dom_ready')

    let instagram_feed_container = "#instagram-feed"
    let $instagram_feed = $(instagram_feed_container)
    if($instagram_feed.length) {
        $.instagramFeed({
            'username': $instagram_feed.data('username'),
            'container': instagram_feed_container,
            'display_profile': true,
            'display_biography': true,
            'display_gallery': true,
            'get_data': false,
            'callback': null,
            'styling': true,
            'items': 12,
            'items_per_row': 3,
            'margin': 1
        })
    }
})
