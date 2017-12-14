# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request


class website_ratings(http.Controller):

    @http.route(['/ratings/read'], type='json', auth="public", methods=['GET'],
                website=True)
    def ratings_read(self, object_model, object_id):
        """
        Lee el rating de un objecto
        """
        cr, uid, context, registry, website = request.cr, request.uid, \
            request.context, request.registry, request.website

        orm_ratings = registry.get('website_ratings.ratings')
        orm_ratings_user = registry.get('website_ratings.user_rating')

        # leemos rating
        rating = orm_ratings.search(cr, SUPERUSER_ID, [
            ('website_id', '=', website.id),
            ('object_id', '=', object_id),
            ('object_model', '=', object_model)], context=context, limit=1)

        # leemos si el user ya ha hecho rating
        rating_user = orm_ratings_user.search(cr, SUPERUSER_ID, [
            ('website_id', '=', website.id),
            ('object_id', '=', object_id),
            ('object_model', '=', object_model),
            ('user_id', '=', uid)], context=context, limit=1)

        if not rating:
            return {'numbers_of_ratings': 0,
                    'ratings': 0,
                    'send_rating': len(rating_user) > 0}

        row = orm_ratings.read(
            cr, SUPERUSER_ID, rating[0], ['numbers_of_ratings', 'ratings'],
            context=context)

        data = {'numbers_of_ratings': row['numbers_of_ratings'],
                'ratings': row['ratings'],
                'send_rating': len(rating_user) > 0}

        return data

    @http.route(['/ratings/send'], type='json', auth="public",
                methods=['POST'], website=True)
    def ratings_send(self, object_model, object_id, rating):
        cr, uid, context, registry, website = request.cr, request.uid, \
            request.context, request.registry, request.website

        orm_ratings = registry.get('website_ratings.ratings')
        orm_ratings_user = registry.get('website_ratings.user_rating')

        # chequeamos parametro rating
        try:
            rating = float(rating)
        except ValueError:
            return {'error': True,
                    'msm': u'Valor para rating no válido'}

        if not (0 <= rating <= 5):
            return {'error': True,
                    'msm': u'Valor para rating debe estar entre 0 y 5'}

        # chequeamos parametros objecto
        try:
            object_id = int(object_id)
        except ValueError:
            return {'error': True, 'msm': u'Valor para object_id no válido'}
        try:
            orm_object = registry.get(object_model)
        except:
            return {'error': True, 'msm': u'Valor para object_model no válido'}

        object_id_search = orm_object.search(
            cr, SUPERUSER_ID, [('id', '=', object_id)], limit=1)

        if not object_id_search:
            return {'error': True, 'msm': u'Object no found'}

        # leemos si el user ya ha hecho rating
        rating_user = orm_ratings_user.search(cr, SUPERUSER_ID, [
            ('website_id', '=', website.id),
            ('object_id', '=', object_id),
            ('object_model', '=', object_model),
            ('user_id', '=', uid)], context=context, limit=1)

        if rating_user:
            return {'error': True,
                    'msm': u'El usuario ya ha hecho un rating sobre '
                           u'este objeto'}

        # guardamos el rating de los usuarios
        orm_ratings_user.create(cr, SUPERUSER_ID, {
            'website_id': website.id,
            'user_id': uid,
            'object_id': object_id,
            'object_model': object_model,
            'rating': rating,
        })

        # actualizamos el rating global
        cr.execute('''
            select  object_model, object_id, avg(rating) as avg,
                    count(*) as count
            from    website_ratings_user_rating
            where   object_model = '%s' and object_id = %d
            group   by object_model, object_id
            order   by object_model, object_id
        ''' % (object_model, object_id))

        row = cr.fetchone()

        rating_id = orm_ratings.search(cr, SUPERUSER_ID, [
            ('website_id', '=', website.id),
            ('object_id', '=', object_id),
            ('object_model', '=', object_model)], context=context, limit=1)
        if not rating_id:
            orm_ratings.create(cr, SUPERUSER_ID, {
                'website_id': website.id,
                'object_model': row[0],
                'object_id': row[1],
                'ratings': row[2],
                'numbers_of_ratings': row[3],
            })
        else:
            orm_ratings.write(cr, SUPERUSER_ID, rating_id[0], {
                'ratings': row[2],
                'numbers_of_ratings': row[3],
            })

        return {'numbers_of_ratings': row[3],
                'ratings': row[2]}
