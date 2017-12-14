document.addEventListener('DOMContentLoaded', function(){
    (function ($) {

        $.fn.shareButtons = function (url, options) {

            // The URL is optional. If it is omitted, the plugin
            // will use the URL of the current page.

            if(typeof url === 'object') {
                options = url;
                url = window.location.href;
            }

            options = $.extend({
                twitter : false,
                facebook : false,
                googlePlus : false,
                pinterest: false,
                tumblr: false
            }, options);


            var url_encoded = encodeURIComponent(url);


            // The URLs of the share pages for the supported services

            var shareURLs = {
                'twitter' : 'https://twitter.com/intent/tweet?url=' + url_encoded,
                'facebook' : 'https://facebook.com/sharer.php?u=' + url_encoded,
                'googlePlus' : 'https://plus.google.com/share?url=' + url_encoded,
                'tumblr' : 'http://www.tumblr.com/share/link?url=' + url_encoded,
                'pinterest': 'https://pinterest.com/pin/create/button?url=' + url_encoded
            };

            // Twitter, Facebook, Tumblr and Pinterest support more options, unique for their services.
            // We handle them here and add them to the sharing URLs.

            // Twitter supports:
            // options.twitter.text - Default text of the tweet. The user can change it.
            // options.twitter.via - A screen name to associate with the Tweet. (By default: none)

            if(options.twitter) {

                if (options.twitter.text) {
                    shareURLs['twitter'] += '&text=' + encodeURIComponent(options.twitter.text);
                }

                if (options.twitter.via) {
                    shareURLs['twitter'] += '&via=' + encodeURIComponent(options.twitter.via);
                }

            }

            // Facebook supports:
            // options.facebook.name - Title of the post (By default: none)

            if(options.facebook) {

                if (options.facebook.name) {
                    shareURLs['facebook'] += '&t=' + encodeURIComponent(options.facebook.name);
                }

            }

            // Tumblr supports:
            // options.tumblr.name - Title of the post (By default: none)
            // options.tumblr.description - Description of the post (By default: none)

            if(options.tumblr) {

                if (options.tumblr.name) {
                    shareURLs['tumblr'] += '&name=' + encodeURIComponent(options.tumblr.name);
                }

                if (options.tumblr.description) {
                    shareURLs['tumblr'] += '&description=' + encodeURIComponent(options.tumblr.description);
                }

            }

            // You can only share images on Pinterest, supplied by the media parameter. It also
            // supports descriptions, which we've included in the URL.

            if(options.pinterest) {

                if (options.pinterest.media) {
                    shareURLs['pinterest'] += '&media=' + encodeURIComponent(options.pinterest.media);
                }

                if (options.pinterest.description) {
                    shareURLs['pinterest'] += '&description=' + encodeURIComponent(options.pinterest.description);
                }

            }

            // The plugin supports multiple share buttons on the page.
            // Here we loop the supplied elements and initialize it.

            this.each(function(i){

                var elem = $(this);

                if(options.twitter){
                    button = elem.find('.btn-social-share-twitter');
                    if( button.length == 0 ) {
                        elem.append($('<a class="btn-social-share btn-social-share-twitter" href="' + shareURLs.twitter + '" ><i class="fa fa-twitter"></i></a>'));
                    } else {
                        button.attr('href', shareURLs.twitter);
                    }
                }

                if(options.facebook){
                    button = elem.find('.btn-social-share-facebook');
                    if( button.length == 0 ) {
                        elem.append($('<a class="btn-social-share btn-social-share-facebook" href="' + shareURLs.facebook +  '" ><i class="fa fa-facebook"></i></a>'));
                    } else {
                        button.attr('href', shareURLs.facebook);
                    }
                }

                if(options.googlePlus){
                    button = elem.find('.btn-social-share-google-plus');
                    if( button.length == 0 ) {
                        elem.append($('<a class="btn-social-share btn-social-share-google-plus" href="' + shareURLs.googlePlus +  '" ><i class="fa fa-google-plus"></i></a>'));
                    } else {
                        button.attr('href', shareURLs.googlePlus);
                    }
                }

                if(options.pinterest){
                    button = elem.find('.btn-social-share-pinterest');
                    if( button.length == 0 ) {
                        elem.append($('<a class="btn-social-share btn-social-share-pinterest" href="' + shareURLs.pinterest +  '" ><i class="fa fa-pinterest"></i></a>'));
                    } else {
                        button.attr('href', shareURLs.pinterest);
                    }
                }

                if(options.tumblr){
                    button = elem.find('.btn-social-share-tumblr');
                    if( button.length == 0 ) {
                        elem.append($('<a class="btn-social-share btn-social-share-tumblr" href="' + shareURLs.tumblr +  '" ><i class="fa fa-tumblr"></i></a>'));
                    } else {
                        button.attr('href', shareURLs.tumblr);
                    }
                }

            });

            // When a social icon is clicked, open a window with the share URL, centered on screen.

            $(this).find('a').click(function(e) {

                e.preventDefault();

                var url = this.href,
                    width = 500,
                    height = 400,
                    left = (screen.width / 2) - (width / 2),
                    top = (screen.height / 2) - (height / 2);

                window.open(url, 'Social Share', 'toolbar=no, location=no, directories=no, status=no,' +
                    ' menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=' + width + ', height=' + height + ', top=' + top + ', left=' + left);
            });

            return this;
        };

    })(jQuery);

    jQuery(document).ready(function($){
        $('*[data-bind="social-share-buttons"]').each(function(e){
            // TODO: Check if target attributes exists, otherwise try to get data from other tags/attributes
            var options = {

                twitter: {
                    text: $('meta[name="twitter:description"]').attr('content'),
                    via: $('meta[name="twitter:site"]').attr('content')
                },

                facebook: {
                    name: $('meta[property="og:title"]').attr('content')
                },

                googlePlus : true,

                tumblr: {
                    name: $('meta[property="og:title"]').attr('content'),
                    description: $('meta[property="og:description"]').attr('content')
                },

                pinterest: {
                    media: $('meta[property="og:image"]').attr('content'),
                    description: $('meta[property="og:description"]').attr('content')
                }
            };
            $(this).shareButtons(options);
        });
    });
});
