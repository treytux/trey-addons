###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import HttpCase


class AuthorProfileControllerTest(HttpCase):

    def test_valid_author_profile(self):
        author = self.env['res.partner'].create({
            'name': 'Test Author',
            'author_description': 'Author description',
        })
        response = self.url_open(f'/author/profile/{author.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Author', response.text)
        self.assertIn('Author description', response.text)

    def test_invalid_author_profile(self):
        response = self.url_open('/author/profile/300')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Author Not Found', response.text)
        self.assertIn('300', response.text)

    def test_author_without_blog_posts(self):
        author = self.env['res.partner'].create({
            'name': 'Author',
            'author_description': 'No posts yet',
        })
        response = self.url_open(f'/author/profile/{author.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Author', response.text)
        self.assertIn('No posts yet', response.text)

    def test_author_posts_filtering(self):
        author1 = self.env['res.partner'].create({
            'name': 'Author One',
            'author_description': 'First author',
        })
        author2 = self.env['res.partner'].create({
            'name': 'Author Two',
            'author_description': 'Second author',
        })
        Post = self.env['blog.post']
        post1 = Post.create({
            'name': 'Post by Author One',
            'author_id': author1.id,
        })
        self.assertTrue(post1)
        post2 = Post.create({
            'name': 'Post by Author Two',
            'author_id': author2.id,
        })
        self.assertTrue(post2)
        response = self.url_open(f'/author/profile/{author1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Post by Author One', response.text)
        self.assertNotIn('Post by Author Two', response.text)
