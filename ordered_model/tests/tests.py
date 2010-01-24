from django.test import TestCase
from ordered_model.tests.models import Item

class ModelTestCase(TestCase):
    fixtures = ['test_items.json']
    
    def assertNames(self, names):
        self.assertEqual(names, [i.name for i in Item.objects.all()])
    
    def test_inserting_new_models(self):
        Item.objects.create(name='Wurble')
        self.assertNames(['1', '2', '3', '4', 'Wurble'])
    
    def test_move_up(self):
        Item.objects.get(pk=4).move_up()
        self.assertNames(['1', '2', '4', '3'])
        Item.objects.get(pk=1).move_up()
        self.assertNames(['1', '2', '4', '3'])
    
    def test_move_up_with_gap(self):
        Item.objects.get(pk=3).move_up()
        self.assertNames(['1', '3', '2', '4'])
    
    def test_move_down(self):
        Item.objects.get(pk=1).move_down()
        self.assertNames(['2', '1', '3', '4'])
        Item.objects.get(pk=4).move_down()
        self.assertNames(['2', '1', '3', '4'])
    
    def test_move_down_with_gap(self):
        Item.objects.get(pk=2).move_down()
        self.assertNames(['1', '3', '2', '4'])
    
    def test_delete(self):
        Item.objects.get(pk=2).delete()
        self.assertNames(['1', '3', '4'])
        Item.objects.get(pk=3).move_up()
        self.assertNames(['3', '1', '4'])

