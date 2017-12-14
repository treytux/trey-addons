(function () {
    'use strict';

    var _t = openerp._t, website = openerp.website;

    openerp.website.CommentRating = openerp.Widget.extend({

        init: function(parent) {
            this._super(parent);
        },
        start: function() {
            var self = this;

            self.rating_name = self.$el.parent().data('input_name');
            self.$el.parent().find('ul').attr('name', self.rating_name);
            self.el_ratings = self.$el.parent().find("li.star-rating");
            self.span_number_ratings = self.$el.parent().find("span.star-rating-count");
            self.span_ratings = self.$el.parent().find("span.ratings-value");
            self.ratings = self.$el.parent().data('ratings');
            self.numbers_of_ratings = self.$el.parent().data('numbers_of_ratings') ? self.$el.parent().data('numbers_of_ratings') : 0;
            self.update_rating();
            self.$el.parent().find('a').on('click', function(event) {
                event.preventDefault();
                self.ratings = $(this).data('star');
                self.update_rating();
                $('select.select-invisible').val($(this).data('star'));
            });

            $('.product-rating-disabled').on('click', function(e){
                e.preventDefault();
            });

            $('form#comment a.a-submit').on('click', function(e){
                e.preventDefault();
                if($(this).parent().find('textarea.form-control').val() == "") {
                    $('span.text-comment-empty').removeAttr('style');
                    $('.a-submit').text('Post');
                }
                $('.a-submit').text('Post');

            });

            $('form#comment textarea.form-control').on('change keyup paste', function() {
                if($(this).val() != ""){
                    $('span.text-comment-empty').css("display", "none");
                    $('.a-submit').removeAttr('disabled');
                    $('.a-submit').removeClass('disabled');
                }
            });

            $('form#comment').on('submit', function(e){
                if ($('form#comment textarea.form-control').val() == '') {
                    e.preventDefault();
                }
            });

            self._super();
        },
        update_rating: function () {
            var self = this;
            var rating = Math.round(self.ratings);
            self.el_ratings.removeClass('star-rating-on');
            if (rating > 0) {
                for(var i=0; i<=5; i++) {
                    if (i <= rating) {
                        var input = self.el_ratings[i-1];
                        $(input).addClass('star-rating-on');
                    }
                }
            }
            self.span_number_ratings.html(self.numbers_of_ratings);
            self.span_ratings.html(String(Math.round(self.ratings*100)/100));
        },
    });

    openerp.website.ready().done(function() {
        $('div.comment-ratings').each(function() {
            new openerp.website.CommentRating().appendTo($(this));
        });
    });
})();
