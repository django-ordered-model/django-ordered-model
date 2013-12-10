from django.test import TestCase
from ordered_model.tests.models import Answer, Item, Question


class OrderGenerationTests(TestCase):
    def test_second_order_generation(self):
        first_item = Item.objects.create()
        self.assertEqual(first_item.order, 0)
        second_item = Item.objects.create()
        self.assertEqual(second_item.order, 1)


class ModelTestCase(TestCase):
    fixtures = ['test_items.json']

    def assertNames(self, names):
        self.assertEqual(names, [(i.name, i.order) for i in Item.objects.all()])

    def test_inserting_new_models(self):
        Item.objects.create(name='Wurble')
        self.assertNames([('1', 0), ('2', 1), ('3', 5), ('4', 6), ('Wurble', 7)])

    def test_up(self):
        Item.objects.get(pk=4).up()
        self.assertNames([('1', 0), ('2', 1), ('4', 5), ('3', 6)])

    def test_up_first(self):
        Item.objects.get(pk=1).up()
        self.assertNames([('1', 0), ('2', 1), ('3', 5), ('4', 6)])

    def test_up_with_gap(self):
        Item.objects.get(pk=3).up()
        self.assertNames([('1', 0), ('3', 1), ('2', 5), ('4', 6)])

    def test_down(self):
        Item.objects.get(pk=1).down()
        self.assertNames([('2', 0), ('1', 1), ('3', 5), ('4', 6)])

    def test_down_last(self):
        Item.objects.get(pk=4).down()
        self.assertNames([('1', 0), ('2', 1), ('3', 5), ('4', 6)])

    def test_down_with_gap(self):
        Item.objects.get(pk=2).down()
        self.assertNames([('1', 0), ('3', 1), ('2', 5), ('4', 6)])

    def test_to(self):
        Item.objects.get(pk=4).to(0)
        self.assertNames([('4', 0), ('1', 1), ('2', 2), ('3', 6)])
        Item.objects.get(pk=4).to(2)
        self.assertNames([('1', 0), ('2', 1), ('4', 2), ('3', 6)])
        Item.objects.get(pk=3).to(1)
        self.assertNames([('1', 0), ('3', 1), ('2', 2), ('4', 3)])

    def test_top(self):
        Item.objects.get(pk=4).top()
        self.assertNames([('4', 0), ('1', 1), ('2', 2), ('3', 6)])
        Item.objects.get(pk=2).top()
        self.assertNames([('2', 0), ('4', 1), ('1', 2), ('3', 6)])

    def test_bottom(self):
        Item.objects.get(pk=1).bottom()
        self.assertNames([('2', 0), ('3', 4), ('4', 5), ('1', 6)])
        Item.objects.get(pk=3).bottom()
        self.assertNames([('2', 0), ('4', 4), ('1', 5), ('3', 6)])

    def test_above(self):
        Item.objects.get(pk=3).above(Item.objects.get(pk=1))
        self.assertNames([('3', 0), ('1', 1), ('2', 2), ('4', 6)])
        Item.objects.get(pk=4).above(Item.objects.get(pk=1))
        self.assertNames([('3', 0), ('4', 1), ('1', 2), ('2', 3)])

    def test_above_self(self):
        Item.objects.get(pk=3).above(Item.objects.get(pk=3))
        self.assertNames([('1', 0), ('2', 1), ('3', 5), ('4', 6)])

    def test_below(self):
        Item.objects.get(pk=1).below(Item.objects.get(pk=3))
        self.assertNames([('2', 0), ('3', 4), ('1', 5), ('4', 6)])
        Item.objects.get(pk=3).below(Item.objects.get(pk=4))
        self.assertNames([('2', 0), ('1', 4), ('4', 5), ('3', 6)])

    def test_below_self(self):
        Item.objects.get(pk=2).below(Item.objects.get(pk=2))
        self.assertNames([('1', 0), ('2', 1), ('3', 5), ('4', 6)])

    def test_delete(self):
        Item.objects.get(pk=2).delete()
        self.assertNames([('1', 0), ('3', 5), ('4', 6)])
        Item.objects.get(pk=3).up()
        self.assertNames([('3', 0), ('1', 5), ('4', 6)])


class OrderWithRespectToTests(TestCase):
    def setUp(self):
        q1 = Question.objects.create()
        q2 = Question.objects.create()
        self.q1_a1 = q1.answers.create()
        self.q2_a1 = q2.answers.create()
        self.q1_a2 = q1.answers.create()
        self.q2_a2 = q2.answers.create()

    def test_saved_order(self):
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a1.pk, 0), (self.q1_a2.pk, 1),
            (self.q2_a1.pk, 0), (self.q2_a2.pk, 1)
        ])

    def test_swap(self):
        with self.assertRaises(ValueError):
            self.q1_a1.swap([self.q2_a1])

    def test_up(self):
        self.q1_a2.up()
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a2.pk, 0), (self.q1_a1.pk, 1),
            (self.q2_a1.pk, 0), (self.q2_a2.pk, 1)
        ])

    def test_down(self):
        self.q2_a1.down()
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a1.pk, 0), (self.q1_a2.pk, 1),
            (self.q2_a2.pk, 0), (self.q2_a1.pk, 1)
        ])

    def test_to(self):
        self.q2_a1.to(1)
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a1.pk, 0), (self.q1_a2.pk, 1),
            (self.q2_a2.pk, 0), (self.q2_a1.pk, 1)
        ])

    def test_above(self):
        with self.assertRaises(ValueError):
            self.q1_a2.above(self.q2_a1)
        self.q1_a2.above(self.q1_a1)
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a2.pk, 0), (self.q1_a1.pk, 1),
            (self.q2_a1.pk, 0), (self.q2_a2.pk, 1)
        ])

    def test_below(self):
        with self.assertRaises(ValueError):
            self.q2_a1.below(self.q1_a2)
        self.q2_a1.below(self.q2_a2)
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a1.pk, 0), (self.q1_a2.pk, 1),
            (self.q2_a2.pk, 0), (self.q2_a1.pk, 1)
        ])

    def test_top(self):
        self.q1_a2.top()
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a2.pk, 0), (self.q1_a1.pk, 1),
            (self.q2_a1.pk, 0), (self.q2_a2.pk, 1)
        ])

    def test_bottom(self):
        self.q2_a1.bottom()
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_a1.pk, 0), (self.q1_a2.pk, 1),
            (self.q2_a2.pk, 0), (self.q2_a1.pk, 1)
        ])
