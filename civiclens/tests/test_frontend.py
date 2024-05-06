from django.test import Client
# from django.conf import settings
from regulations.forms import Search

client = Client()

def test_homepage_exists():
    response = client.get(path="/")
    assert response.status_code == 200

# def test_view_url_accessible_by_name(self):
#     response = self.client.get(reverse('authors'))
#     self.assertEqual(response.status_code, 200)

# def test_view_uses_correct_template(self):
#     response = self.client.get(reverse('authors'))
#     self.assertEqual(response.status_code, 200)
#     self.assertTemplateUsed(response, 'catalog/author_list.html')

# def test_pagination_is_ten(self):
#     response = self.client.get(reverse('authors'))
#     self.assertEqual(response.status_code, 200)
#     self.assertTrue('is_paginated' in response.context)
#     self.assertTrue(response.context['is_paginated'] == True)
#     self.assertEqual(len(response.context['author_list']), 10)

# def test_lists_all_authors(self):
#     # Get second page and confirm it has (exactly) remaining 3 items
#     response = self.client.get(reverse('authors')+'?page=2')
#     self.assertEqual(response.status_code, 200)
#     self.assertTrue('is_paginated' in response.context)
#     self.assertTrue(response.context['is_paginated'] == True)
#     self.assertEqual(len(response.context['author_list']), 3)



# class SearchTestCase(TestCase):
#     def setUp(self):
#         Search.objects.create(search_term="gun control")
#         Search.objects.create(search_term="reproductive health")

#         

#     def test_search_term_appearing(self):
#         """Animals that can speak are correctly identified"""
#         gun_control = Search.objects.get(search_term="gun control")
#         reproductive_health = Search.objects.get(search_term="reproductive health")
#         self.assertEqual(client.get(), gun_control.search_term)
#         self.assertEqual(client.get(), reproductive_health.search_term)

