from django.test import TestCase
from ordered_model.tests.models import Item, ItemLeft, ItemRight, ItemsLeftRight

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


    def assertNamesM2M(self, names, item_left_id):
        ilr = ItemsLeftRight.objects.filter(item_left__id=item_left_id)
        self.assertEqual(names, [i.item_right.name for i in ilr])

    def test_inserting_new_models_m2m(self):
        il = ItemLeft.objects.get(pk=1)
        ir = ItemRight.objects.create(name='Lorem')
        ilr = ItemsLeftRight(item_left=il, item_right=ir)
        ilr.save()
        self.assertNamesM2M(['1', '2', '3', '4', 'Lorem'], 1)
        self.assertNamesM2M(['5', '6', '7', '8'], 2)

    def test_move_up_m2m(self):
        ItemsLeftRight.objects.get(pk=4).move_up()
        self.assertNamesM2M(['1', '2', '4', '3'], 1)
        ItemsLeftRight.objects.get(pk=1).move_up()
        self.assertNamesM2M(['1', '2', '4', '3'], 1)

    def test_move_up_with_gap_m2m(self):
        ItemsLeftRight.objects.get(pk=3).move_up()
        self.assertNamesM2M(['1', '3', '2', '4'], 1)

    def test_move_down_m2m(self):
        ItemsLeftRight.objects.get(pk=1).move_down()
        self.assertNamesM2M(['2', '1', '3', '4'], 1)
        ItemsLeftRight.objects.get(pk=4).move_down()
        self.assertNamesM2M(['2', '1', '3', '4'], 1)

    def test_move_down_with_gap_m2m(self):
        ItemsLeftRight.objects.get(pk=2).move_down()
        self.assertNamesM2M(['1', '3', '2', '4'], 1)

    def test_delete_m2m(self):
        ItemsLeftRight.objects.get(pk=2).delete()
        self.assertNamesM2M(['1', '3', '4'], 1)
        ItemsLeftRight.objects.get(pk=3).move_up()
        self.assertNamesM2M(['3', '1', '4'], 1)

