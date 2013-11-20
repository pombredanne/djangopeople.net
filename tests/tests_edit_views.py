import os
import shutil
import hashlib

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.conf import settings

from tagging.utils import edit_string_for_tags

from djangopeople.djangopeople.models import DjangoPerson, Country
from djangopeople.machinetags.utils import tagdict


class EditViewTest(TestCase):
    fixtures = ['test_data']

    def setUp(self):  # noqa
        super(EditViewTest, self).setUp()
        self.client.login(username='daveb', password='123456')

        img_content = open(os.path.join(settings.OUR_ROOT,
                                        'djangopeople/fixtures/pony.gif'),
                           'rb').read()
        sha1sum = hashlib.sha1(img_content).hexdigest()
        self.hashed_upload_img_file_name = os.path.join(sha1sum[:1],
                                                        sha1sum[1:2], sha1sum)

        # make sure the profile upload folder exists
        self.profile_img_path = os.path.join(settings.MEDIA_ROOT, 'profiles')
        if not os.path.exists(self.profile_img_path):
            os.makedirs(self.profile_img_path)

    def tearDown(self):  # noqa
        # remove uploaded profile picture
        if os.path.exists(self.profile_img_path):
            shutil.rmtree(self.profile_img_path)

    def test_edit_finding_permissions(self):
        '''
        logged in user can only edit his own skills
        '''
        url = reverse('edit_finding', args=['daveb'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        url = reverse('edit_finding', args=['satchmo'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_edit_finding_initial_data(self):
        url_edit_finding = reverse('edit_finding', args=['daveb'])
        p = DjangoPerson.objects.get(user__username='daveb')
        mtags = tagdict(p.machinetags.all())

        response = self.client.get(url_edit_finding)

        self.assertContains(response, mtags['profile']['looking_for_work'])
        self.assertContains(response, mtags['im']['django'])
        self.assertContains(response, p.user.email)

    def test_edit_finding_email(self):
        url_edit_finding = reverse('edit_finding', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        new_email = 'foo@bar.com'
        data = {'email': new_email,
                'first_name': 'Test',
                'last_name': 'User',
                'privacy_search': 'public',
                'privacy_email': 'private',
                'privacy_im': 'private',
                'privacy_irctrack': 'public'}

        u = User.objects.get(username='daveb')
        self.assertNotEqual(u.first_name, 'Test')
        self.assertNotEqual(u.last_name, 'User')

        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertRedirects(response, url_profile)
        self.assertContains(response, new_email)

        u = User.objects.get(username='daveb')
        self.assertEqual(u.email, new_email)
        self.assertEqual(u.first_name, 'Test')
        self.assertEqual(u.last_name, 'User')

    def test_edit_finding_looking_for_work(self):
        url_edit_finding = reverse('edit_finding', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        new_email = 'foo@bar.com'
        looking_for_work = 'freelance'
        data = {'looking_for_work': looking_for_work,
                'email': new_email,
                'first_name': 'Hello',
                'last_name': 'World',
                'privacy_search': 'public',
                'privacy_email': 'private',
                'privacy_im': 'private',
                'privacy_irctrack': 'public'}

        p = DjangoPerson.objects.get(user__username='daveb')
        mtags = tagdict(p.machinetags.all())
        self.assertEqual(mtags['profile']['looking_for_work'], 'full-time')

        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertRedirects(response, url_profile)

        p = DjangoPerson.objects.get(user__username='daveb')
        mtags = tagdict(p.machinetags.all())
        self.assertEqual(mtags['profile']['looking_for_work'], 'freelance')

        # check initial value
        response = self.client.get(url_edit_finding)
        self.assertContains(response, looking_for_work)

    def test_edit_finding_im(self):
        url_edit_finding = reverse('edit_finding', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        new_email = 'foo@bar.com'
        im_jabber = 'daveb@jabber.org'
        data = {'im_jabber': im_jabber,
                'email': new_email,
                'first_name': 'Hello',
                'last_name': 'World',
                'privacy_search': 'public',
                'privacy_email': 'private',
                'privacy_im': 'private',
                'privacy_irctrack': 'public'}

        p = DjangoPerson.objects.get(user__username='daveb')
        mtags = tagdict(p.machinetags.all())
        self.assertEqual(mtags['im']['jabber'], '')

        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertRedirects(response, url_profile)

        p = DjangoPerson.objects.get(user__username='daveb')
        mtags = tagdict(p.machinetags.all())
        self.assertEqual(mtags['im']['jabber'], im_jabber)

        # check initial value
        response = self.client.get(url_edit_finding)
        self.assertContains(response, im_jabber)

    def test_edit_finding_services(self):
        url_edit_finding = reverse('edit_finding', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        service_twitter = 'https://twitter.com/davebbar'
        data = {'service_twitter': service_twitter,
                'email': 'foo@bar.com',
                'first_name': 'Hello',
                'last_name': 'World',
                'privacy_search': 'public',
                'privacy_email': 'private',
                'privacy_im': 'private',
                'privacy_irctrack': 'public'}

        p = DjangoPerson.objects.get(user__username='daveb')
        mtags = tagdict(p.machinetags.all())
        self.assertEqual(mtags['services']['twitter'], '')

        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertRedirects(response, url_profile)

        p = DjangoPerson.objects.get(user__username='daveb')
        mtags = tagdict(p.machinetags.all())
        self.assertEqual(mtags['services']['twitter'], service_twitter)

        # check initial value
        response = self.client.get(url_edit_finding)
        self.assertContains(response, service_twitter)

    def test_edit_finding_form_error_email_validation(self):
        url_edit_finding = reverse('edit_finding', args=['daveb'])

        u = User.objects.get(username='daveb')
        old_email = u.email
        other_user = User.objects.get(username='satchmo')

        # set new email for daveb to existing email of user satchmo
        data = {'email': other_user.email,
                'privacy_search': 'public',
                'privacy_email': 'private',
                'privacy_im': 'private',
                'privacy_irctrack': 'public'}

        u = User.objects.get(username='daveb')
        self.assertEqual(u.email, old_email)

        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'That e-mail is already in use')

        u = User.objects.get(username='daveb')
        self.assertEqual(u.email, old_email)

    def test_edit_finding_form_error_fields_required(self):
        url_edit_finding = reverse('edit_finding', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        data = {'email': 'foo@bar.com',
                'first_name': 'Hello',
                'last_name': 'World',
                'privacy_search': 'public',
                'privacy_email': 'private',
                'privacy_im': 'private',
                'privacy_irctrack': 'public'}

        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertRedirects(response, url_profile)

        data.pop('email')
        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')

        data.pop('privacy_search')
        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_search',
                             'This field is required.')

        data.pop('privacy_email')
        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_search',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_email',
                             'This field is required.')

        data.pop('privacy_im')
        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_search',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_email',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_im',
                             'This field is required.')

        data.pop('privacy_irctrack')
        response = self.client.post(url_edit_finding, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_search',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_email',
                             'This field is required.')
        self.assertFormError(response, 'form', 'privacy_irctrack',
                             'This field is required.')

    def test_edit_skill_permission(self):
        '''
        logged in user can only edit his own skills
        '''
        url_edit_skills = reverse('edit_skills', args=['daveb'])
        response = self.client.get(url_edit_skills)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url_edit_skills)
        self.assertEqual(response.status_code, 302)

        url_edit_skills = reverse('edit_skills', args=['satchmo'])
        response = self.client.get(url_edit_skills)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(url_edit_skills)
        self.assertEqual(response.status_code, 403)

    def test_add_skills(self):
        '''
        test adding skills
        '''
        url_edit_skills = reverse('edit_skills', args=['daveb'])

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(len(p.skilltags), 3)
        self.assertTrue('jazz' in edit_string_for_tags(p.skilltags))
        self.assertTrue('linux' in edit_string_for_tags(p.skilltags))
        self.assertTrue('python' in edit_string_for_tags(p.skilltags))

        skills = '%s django' % (edit_string_for_tags(p.skilltags))
        self.client.post(url_edit_skills, {'skills': skills})

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(len(p.skilltags), 4)
        self.assertTrue('jazz' in edit_string_for_tags(p.skilltags))
        self.assertTrue('linux' in edit_string_for_tags(p.skilltags))
        self.assertTrue('python' in edit_string_for_tags(p.skilltags))
        self.assertTrue('django' in edit_string_for_tags(p.skilltags))

    def test_delete_skill(self):
        '''
        test deleting skills
        '''
        url_edit_skills = reverse('edit_skills', args=['daveb'])

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(len(p.skilltags), 3)
        self.assertTrue('jazz' in edit_string_for_tags(p.skilltags))
        self.assertTrue('linux' in edit_string_for_tags(p.skilltags))
        self.assertTrue('python' in edit_string_for_tags(p.skilltags))

        # delete jazz skill
        skills = 'linux python'
        self.client.post(url_edit_skills, {'skills': skills})
        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(len(p.skilltags), 2)
        self.assertTrue('linux' in edit_string_for_tags(p.skilltags))
        self.assertTrue('python' in edit_string_for_tags(p.skilltags))
        self.assertFalse('jazz' in edit_string_for_tags(p.skilltags))

        # delete all skills
        self.client.post(url_edit_skills, {'skills': ''})
        p = DjangoPerson.objects.get(user__username='daveb')

        self.assertEqual(len(p.skilltags), 0)
        self.assertEqual(edit_string_for_tags(p.skilltags), '')

    def test_edit_account_permission(self):
        '''
        logged in user can only edit his own account
        '''
        url_edit_account = reverse('edit_account', args=['daveb'])
        response = self.client.get(url_edit_account)
        self.assertEqual(response.status_code, 200)

        url_edit_account = reverse('edit_account', args=['satchmo'])
        response = self.client.get(url_edit_account)
        self.assertEqual(response.status_code, 403)

    def test_edit_account(self):
        '''
        add and change openid
        '''
        url_profile = reverse('user_profile', args=['daveb'])
        url_edit_account = reverse('edit_account', args=['daveb'])

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.openid_server, u'')
        self.assertEqual(p.openid_delegate, u'')

        response = self.client.post(url_edit_account,
                                    {'openid_server': 'http://example.com',
                                     'openid_delegate': 'http://google.com'})

        self.assertRedirects(response, url_profile)

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.openid_server, 'http://example.com/')
        self.assertEqual(p.openid_delegate, 'http://google.com/')

        # test display openid change form (with initial data)
        response = self.client.get(url_edit_account)
        self.assertHTMLEqual(
            response.content.split(
                '<label for="id_openid_server">OpenID server</label>'
            )[1].split('</div>')[0],
            (
                '<input id="id_openid_server" type="text" '
                'name="openid_server" value="http://example.com/" '
                'maxlength="255" />')
        )
        self.assertHTMLEqual(
            response.content.split(
                '<label for="id_openid_delegate">OpenID delegate</label>'
            )[1].split('</div>')[0],
            (
                '<input id="id_openid_delegate" '
                'type="text" name="openid_delegate" '
                'value="http://google.com/" '
                'maxlength="255" />'
            )
        )

        # test change openid settings
        response = self.client.post(url_edit_account,
                                    {'openid_server': 'http://test.com',
                                     'openid_delegate': 'http://yahoo.com'})

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.openid_server, 'http://test.com/')
        self.assertEqual(p.openid_delegate, 'http://yahoo.com/')

    def test_edit_account_form_error(self):
        '''
        check AccountForm error messages
        '''
        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.openid_server, u'')
        self.assertEqual(p.openid_delegate, u'')

        url_edit_account = reverse('edit_account', args=['daveb'])
        response = self.client.post(url_edit_account,
                                    {'openid_server': 'example',
                                     'openid_delegate': 'fooBar'})

        self.assertEqual(response.status_code, 200)

        self.assertFormError(response, 'form', 'openid_server',
                             'Enter a valid URL.')
        self.assertFormError(response, 'form', 'openid_delegate',
                             'Enter a valid URL.')

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.openid_server, u'')
        self.assertEqual(p.openid_delegate, u'')

    def test_change_portfolio_entry(self):
        url_profile = reverse('user_profile', args=['daveb'])
        url_edit_portfolio = reverse('edit_portfolio', args=['daveb'])
        response = self.client.get(url_profile)
        self.assertContains(response, '<li><a href="http://example.org/" '
                                      'class="url" rel="nofollow"><cite>'
                                      'cheese-shop</cite></a></li>')

        # test change existing portfolio entry
        response = self.client.post(url_edit_portfolio,
                                    {'title_1': 'chocolate shop',
                                     'url_1': 'cs.org'}, follow=True)
        self.assertRedirects(response, url_profile)
        self.assertNotContains(response, '<li><a href="http://example.org/" '
                                         'class="url" rel="nofollow"><cite>'
                                         'cheese-shop</cite></a></li>')
        self.assertContains(response, '<li><a href="http://cs.org/" class="url'
                                      '" rel="nofollow"><cite>chocolate shop'
                                      '</cite></a></li>')

    def test_remove_portfolio_entry(self):
        # test remove existing portfolio entry
        url_profile = reverse('user_profile', args=['daveb'])
        url_edit_portfolio = reverse('edit_portfolio', args=['daveb'])
        response = self.client.post(url_edit_portfolio,
                                    {'title_1': '', 'url_1': ''}, follow=True)
        self.assertRedirects(response, url_profile)
        self.assertNotContains(response, '<li><a href="http://example.org/" '
                                         'class="url" rel="nofollow"><cite>'
                                         'cheese-shop</cite></a></li>')
        self.assertNotContains(response, '<li><a href="cs.org/" class="url" '
                                         'rel="nofollow"><cite>chocolate shop'
                                         '</cite></a></li>')
        self.assertContains(response, 'Add some sites')

    def test_add_portfolio_entry(self):
        # test add new portfolio entry

        url_profile = reverse('user_profile', args=['daveb'])
        url_edit_portfolio = reverse('edit_portfolio', args=['daveb'])
        response = self.client.post(url_edit_portfolio,
                                    {'title_1': 'chocolate shop',
                                     'url_1': 'cs.org'},
                                    follow=True)
        self.assertRedirects(response, url_profile)
        self.assertNotContains(response, 'Add some sites')
        self.assertContains(response, '<li><a href="http://cs.org/" class="url'
                                      '" rel="nofollow"><cite>chocolate shop'
                                      '</cite></a></li>')

    def test_portfolio_form_url_error(self):
        # test portfolio edit form
        url_edit_portfolio = reverse('edit_portfolio', args=['daveb'])
        response = self.client.get(url_edit_portfolio)
        self.assertHTMLEqual(
            response.content.split(
                '<label for="id_title_1">Title 1</label>'
            )[1].split('</div>')[0],
            (
                '<input id="id_title_1" type="text" '
                'name="title_1" value="cheese-shop" '
                'maxlength="100" />'
            )
        )
        self.assertHTMLEqual(
            response.content.split(
                '<label for="id_url_1">URL 1</label>'
            )[1].split('</div>')[0],
            (
                '<input id="id_url_1" type="text" '
                'name="url_1" value="http://example.org/'
                '" maxlength="255" />'
            )
        )
        self.assertHTMLEqual(
            response.content.split(
                '<label for="id_title_2">Title 2</label>'
            )[1].split('</div>')[0],
            (
                '<input id="id_title_2" type="text" '
                'name="title_2" maxlength="100" />'
            )
        )
        self.assertHTMLEqual(
            response.content.split(
                '<label for="id_url_2">URL 2</label>'
            )[1].split('</div>')[0],
            (
                '<input id="id_url_2" type="text" '
                'name="url_2" maxlength="255" />'
            )
        )

        # test form error messages
        response = self.client.post(url_edit_portfolio,
                                    {'title_1': 'chocolate shop',
                                     'url_1': 'no url'},
                                    follow=True)

        self.assertFormError(response, 'form', 'url_1', 'Enter a valid URL.')

    def test_edit_other_user(self):
        # test editing another users portfolio

        # add new user
        user = User.objects.create_user('testuser', 'foo@example.com', 'pass')
        DjangoPerson.objects.create(
            user=user,
            country=Country.objects.get(pk=1),
            latitude=44,
            longitude=2,
            location_description='Somewhere',
        )

        url_profile = reverse('user_profile', args=['testuser'])
        url_edit_portfolio = reverse('edit_portfolio', args=['testuser'])

        # no Add some sites link for user daveb on testuser's profile page
        response = self.client.get(url_profile)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Add some sites')

        # daveb can't add sites to testuser's portfolio
        response = self.client.post(url_edit_portfolio,
                                    {'title_1': 'chocolate shop',
                                     'url_1': 'cs.org'}, follow=True)
        self.assertEqual(response.status_code, 403)

        response = self.client.get(url_profile)
        self.assertNotContains(response, '<li><a href="http://cs.org/" class="'
                                         'url" rel="nofollow"><cite>chocolate '
                                         'shop </cite></a></li>')

    def test_edit_password_permission(self):
        '''
        logged in user can only edit his own password
        '''
        url_edit_password = reverse('edit_password', args=['daveb'])

        # user can edit his own password
        response = self.client.get(url_edit_password)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url_edit_password)
        self.assertEqual(response.status_code, 200)

        # user can't edit passwords of other users
        url_edit_password = reverse('edit_password', args=['satchmo'])
        response = self.client.get(url_edit_password)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(url_edit_password)
        self.assertEqual(response.status_code, 403)

    def test_edit_password(self):
        '''
        test editing passwords
        '''
        url_edit_password = reverse('edit_password', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        response = self.client.get(url_edit_password)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_password.html')

        u = User.objects.get(username='daveb')
        self.assertTrue(u.check_password('123456'))

        response = self.client.post(url_edit_password,
                                    {'current_password': '123456',
                                     'password1': 'foo',
                                     'password2': 'foo'})

        self.assertRedirects(response, url_profile)
        u = User.objects.get(username='daveb')
        self.assertTrue(u.check_password('foo'))

    def test_edit_password_form_current_password_error(self):
        '''
        test form error messages when current password is invalid
        '''
        url_edit_password = reverse('edit_password', args=['daveb'])

        response = self.client.post(url_edit_password,
                                    {'current_password': 'invalid pw',
                                     'password1': 'foo1',
                                     'password2': 'foo'})

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'current_password',
                             'Please submit your current password.')

    def test_edit_password_form_error_fields_required(self):
        '''
        test form error messages when form fields are empty
        '''
        url_edit_password = reverse('edit_password', args=['daveb'])

        response = self.client.post(url_edit_password, {'password1': 'foo1'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2',
                             'This field is required.')

        response = self.client.post(url_edit_password, {'password2': 'foo1'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password1',
                             'This field is required.')

        response = self.client.post(url_edit_password, {})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password1',
                             'This field is required.')
        self.assertFormError(response, 'form', 'password2',
                             'This field is required.')

    def test_edit_password_form_error_different_passwords(self):
        '''
        test form error message when user submits two different
        passwords
        '''
        url_edit_password = reverse('edit_password', args=['daveb'])

        u = User.objects.get(username='daveb')
        self.assertTrue(u.check_password('123456'))

        # two passwords aren't the same
        response = self.client.post(url_edit_password, {'password1': 'foo1',
                                                        'password2': 'foo'})

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None,
                             'The passwords did not match.')

        u = User.objects.get(username='daveb')
        self.assertTrue(u.check_password('123456'))

    def test_edit_bio_permission(self):
        '''
        logged in user can only edit his own bio
        '''
        url = reverse('edit_bio', args=['daveb'])

        # user can edit his own password
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # user can't edit passwords of other users
        url = reverse('edit_bio', args=['satchmo'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_edit_bio(self):
        '''
        test changing the bio
        '''
        url_edit_bio = reverse('edit_bio', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        response = self.client.get(url_edit_bio)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_bio.html')

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.bio, 'ad')

        bio_string = 'I do a lot of Django stuff'
        response = self.client.post(url_edit_bio,
                                    {'bio': bio_string}, follow=True)

        self.assertRedirects(response, url_profile)
        self.assertContains(response, bio_string)
        self.assertContains(response, 'edit bio')
        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.bio, bio_string)

    def test_delete_bio(self):
        url_edit_bio = reverse('edit_bio', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])
        response = self.client.post(url_edit_bio,
                                    {'bio': ''}, follow=True)

        self.assertRedirects(response, url_profile)
        self.assertContains(response, 'Create your bio')
        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertEqual(p.bio, '')

    def test_edit_location_permission(self):
        '''
        logged in user can only edit his own location
        '''
        url = reverse('edit_location', args=['daveb'])

        # user can edit his own password
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        # user can't edit passwords of other users
        url = reverse('edit_location', args=['satchmo'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_edit_location(self):
        '''
        test changing the location
        '''
        longitude = 14.9853515625
        latitude = 50.0359736721955
        location_description = 'Vienna, Austria'
        country = 12  # id of Austria

        url_edit_location = reverse('edit_location', args=['daveb'])
        url_profile = reverse('user_profile', args=['daveb'])

        response = self.client.get(url_profile)

        self.assertContains(response, 'Austria')
        self.assertContains(response, 'person_latitude = %d' % latitude)
        self.assertContains(response, 'person_longitude = %d' % longitude)

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertTrue(abs(p.latitude - latitude) < 0.01)
        self.assertTrue(abs(p.longitude - longitude) < 0.01)
        self.assertEqual(p.location_description, location_description)
        self.assertEqual(p.country.pk, country)

        response = self.client.get(url_edit_location)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_location.html')

        new_longitude = 153.023071289
        new_latitude = -27.5411533739
        new_location_description = 'Brisbane'
        new_country = 'AU'  # iso code of Australia

        location_dict = {'longitude': new_longitude,
                         'latitude': new_latitude,
                         'location_description': new_location_description,
                         'country': new_country,
                         'region': 'AL'}
        response = self.client.post(url_edit_location, location_dict)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'region',
                             ('The region you selected does not match the '
                              'country'))
        del location_dict['region']

        response = self.client.post(url_edit_location, data=location_dict,
                                    follow=True)

        self.assertRedirects(response, url_profile)
        self.assertNotContains(response, 'Austria')
        self.assertNotContains(response, 'person_latitude = %d' % latitude)
        self.assertNotContains(response, 'person_longitude = %d' % longitude)
        self.assertContains(response, 'Australia')
        self.assertContains(response, 'person_latitude = %d' % new_latitude)
        self.assertContains(response, 'person_longitude = %d' % new_longitude)

        p = DjangoPerson.objects.get(user__username='daveb')
        self.assertTrue(abs(p.latitude - new_latitude) < 0.01)
        self.assertTrue(abs(p.longitude - new_longitude) < 0.01)
        self.assertEqual(p.location_description, new_location_description)
        self.assertEqual(p.country.iso_code, new_country)

    def test_location_bug_24(self):
        # https://github.com/brutasse/djangopeople/issues/24
        url = reverse('edit_location', args=['daveb'])
        data = {
            'location_description': 'Rapid City, South Dakota',
            'country': 'US',
            'latitude': '44.07883004975277',
            'longitude': '-103.28332901005193',
            'region': 'SD',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_edit_location_form_error_fields_required(self):
        url_edit_location = reverse('edit_location', args=['daveb'])

        new_longitude = 153.023071289
        new_latitude = -27.5411533739
        new_location_description = 'Brisbane'
        new_country = 'AU'  # iso code of Australia

        location_dict = {'longitude': new_longitude,
                         'latitude': new_latitude,
                         'location_description': new_location_description,
                         'country': new_country}

        response = self.client.post(url_edit_location, data=location_dict)

        self.assertEqual(response.status_code, 302)

        # remove longitutde
        location_dict.pop('longitude')
        response = self.client.post(url_edit_location, data=location_dict)
        self.assertFormError(response, 'form', 'longitude',
                             'This field is required.')

        # remove latitude
        location_dict.pop('latitude')
        response = self.client.post(url_edit_location, data=location_dict)
        self.assertFormError(response, 'form', 'longitude',
                             'This field is required.')
        self.assertFormError(response, 'form', 'latitude',
                             'This field is required.')

        # remove location_description
        location_dict.pop('location_description')
        response = self.client.post(url_edit_location, data=location_dict)
        self.assertFormError(response, 'form', 'longitude',
                             'This field is required.')
        self.assertFormError(response, 'form', 'latitude',
                             'This field is required.')
        self.assertFormError(response, 'form', 'location_description',
                             'This field is required.')

        # remove country
        location_dict.pop('country')
        response = self.client.post(url_edit_location, data=location_dict)
        self.assertFormError(response, 'form', 'longitude',
                             'This field is required.')
        self.assertFormError(response, 'form', 'latitude',
                             'This field is required.')
        self.assertFormError(response, 'form', 'location_description',
                             'This field is required.')
        self.assertFormError(response, 'form', 'country',
                             'This field is required.')

    def test_edit_loctaion_form_error_invalid_iso_code(self):
        url_edit_location = reverse('edit_location', args=['daveb'])

        new_longitude = 153.023071289
        new_latitude = -27.5411533739
        new_location_description = 'Brisbane'
        new_country = 'XXX'  # invalid iso code

        location_dict = {'longitude': new_longitude,
                         'latitude': new_latitude,
                         'location_description': new_location_description,
                         'country': new_country}

        response = self.client.post(url_edit_location, data=location_dict)

        self.assertFormError(
            response, 'form', 'country',
            'Select a valid choice. XXX is not one of the available choices.'
        )

    def test_edit_location_not_in_the_atlantic(self):
        '''
        test form error message when 43 < lat < 45 and -39 < lon < -33
        '''

        url_edit_location = reverse('edit_location', args=['daveb'])

        new_longitude = -35
        new_latitude = 44
        new_location_description = 'Brisbane'
        new_country = 13  # id of Australia

        location_dict = {'longitude': new_longitude,
                         'latitude': new_latitude,
                         'location_description': new_location_description,
                         'country': new_country}
        response = self.client.post(url_edit_location, data=location_dict)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'location_description',
                             ('Drag and zoom the map until the crosshair '
                              'matches your location'))

    def test_delete_account(self):
        url = reverse('delete_account_request', args=['daveb'])
        response = self.client.get(url)
        self.assertContains(response, "Account deletion")

        response = self.client.post(url, {})
        url = reverse('delete_account_next', args=['daveb'])
        self.assertRedirects(response, url)
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.get(url)
        self.assertContains(response, 'An email was just sent')

        url = mail.outbox[0].body.split('testserver')[2].split('\n')[0]
        response = self.client.get(url)
        self.assertContains(response, 'Account deletion')

        target = response.content.split('action="')[1].split('"', 1)[0]
        self.assertEqual(target, url)

        data = {'password': 'example'}
        response = self.client.post(url, data)
        self.assertContains(response, 'Your password was invalid')

        self.assertEqual(User.objects.count(), 3)
        response = self.client.post(url, {'password': '123456'})
        self.assertEqual(User.objects.count(), 2)

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='daveb')

        url = reverse('delete_account_done', args=['daveb'])
        self.assertRedirects(response, url)

        response = self.client.get(url)
        self.assertContains(response, 'Account deleted')

    def test_failing_deletion(self):
        # expired link: redirect to form
        url = reverse('delete_account',
                      args=['daveb', 'Mg:1Sd7hl:RoSbkTsuqHVUjChAwoB5HZumgCg'])
        response = self.client.get(url, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertContains(response, 'Account deletion')

        # invalid link: 404
        url = reverse('delete_account', args=['daveb', 'test_some_data'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # delete confirmation page only shown if account does not exist
        url = reverse('delete_account_done',
                      args=[User.objects.all()[0].username])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
