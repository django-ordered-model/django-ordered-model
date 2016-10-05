from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.test import TestCase
import uuid
from ordered_model.tests.models import (
    Answer,
    Item,
    Question,
    CustomItem,
    CustomOrderFieldModel,
    Pizza,
    Topping,
    PizzaToppingsThroughModel
)
from ordered_model.tests.models import TestUser
from .admin import ItemAdmin


class OrderGenerationTests(TestCase):
    def test_second_order_generation(self):
        first_item = Item.objects.create()
        self.assertEqual(first_item.order, 0)
        second_item = Item.objects.create()
        self.assertEqual(second_item.order, 1)

class ModelTestCase(TestCase):
    fixtures = ['test_items.json']

    def assertNames(self, names):
        self.assertEqual(list(enumerate(names)), [(i.order, i.name) for i in Item.objects.all()])

    def test_inserting_new_models(self):
        Item.objects.create(name='Wurble')
        self.assertNames(['1', '2', '3', '4', 'Wurble'])

    def test_up(self):
        Item.objects.get(pk=4).up()
        self.assertNames(['1', '2', '4', '3'])

    def test_up_first(self):
        Item.objects.get(pk=1).up()
        self.assertNames(['1', '2', '3', '4'])

    def test_up_with_gap(self):
        Item.objects.get(pk=3).up()
        self.assertNames(['1', '3', '2', '4'])

    def test_down(self):
        Item.objects.get(pk=1).down()
        self.assertNames(['2', '1', '3', '4'])

    def test_down_last(self):
        Item.objects.get(pk=4).down()
        self.assertNames(['1', '2', '3', '4'])

    def test_down_with_gap(self):
        Item.objects.get(pk=2).down()
        self.assertNames(['1', '3', '2', '4'])

    def test_to(self):
        Item.objects.get(pk=4).to(0)
        self.assertNames(['4', '1', '2', '3'])
        Item.objects.get(pk=4).to(2)
        self.assertNames(['1', '2', '4', '3'])
        Item.objects.get(pk=3).to(1)
        self.assertNames(['1', '3', '2', '4'])

    def test_top(self):
        Item.objects.get(pk=4).top()
        self.assertNames(['4', '1', '2', '3'])
        Item.objects.get(pk=2).top()
        self.assertNames(['2', '4', '1', '3'])

    def test_bottom(self):
        Item.objects.get(pk=1).bottom()
        self.assertNames(['2', '3', '4', '1'])
        Item.objects.get(pk=3).bottom()
        self.assertNames(['2', '4', '1', '3'])

    def test_above(self):
        Item.objects.get(pk=3).above(Item.objects.get(pk=1))
        self.assertNames(['3', '1', '2', '4'])
        Item.objects.get(pk=4).above(Item.objects.get(pk=1))
        self.assertNames(['3', '4', '1', '2'])

    def test_above_self(self):
        Item.objects.get(pk=3).above(Item.objects.get(pk=3))
        self.assertNames(['1', '2', '3', '4'])

    def test_below(self):
        Item.objects.get(pk=1).below(Item.objects.get(pk=3))
        self.assertNames(['2', '3', '1', '4'])
        Item.objects.get(pk=3).below(Item.objects.get(pk=4))
        self.assertNames(['2', '1', '4', '3'])

    def test_below_self(self):
        Item.objects.get(pk=2).below(Item.objects.get(pk=2))
        self.assertNames(['1', '2', '3', '4'])

    def test_delete(self):
        Item.objects.get(pk=2).delete()
        self.assertNames(['1', '3', '4'])
        Item.objects.get(pk=3).up()
        self.assertNames(['3', '1', '4'])


class OrderWithRespectToTests(TestCase):
    def setUp(self):
        q1 = Question.objects.create()
        q2 = Question.objects.create()
        u0 = TestUser.objects.create()
        self.q1_a1 = q1.answers.create(user=u0)
        self.q2_a1 = q2.answers.create(user=u0)
        self.q1_a2 = q1.answers.create(user=u0)
        self.q2_a2 = q2.answers.create(user=u0)

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


class CustomPKTest(TestCase):
    def setUp(self):
        self.item1 = CustomItem.objects.create(id=str(uuid.uuid4()), name='1')
        self.item2 = CustomItem.objects.create(id=str(uuid.uuid4()), name='2')
        self.item3 = CustomItem.objects.create(id=str(uuid.uuid4()), name='3')
        self.item4 = CustomItem.objects.create(id=str(uuid.uuid4()), name='4')

    def test_saved_order(self):
        self.assertSequenceEqual(
            CustomItem.objects.values_list('pk', 'order'), [
                (self.item1.pk, 0),
                (self.item2.pk, 1),
                (self.item3.pk, 2),
                (self.item4.pk, 3)
            ]
        )
    
    def test_order_to_extra_update(self):
        modified_time = now()
        self.item1.to(3, extra_update={'modified':modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list('pk', 'order', 'modified'), [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be 
                # handled via auto_now or something
                (self.item1.pk, 3, None)
            ]
        )
    
    def test_bottom_extra_update(self):
        modified_time = now()
        self.item1.bottom(extra_update={'modified':modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list('pk', 'order', 'modified'), [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be 
                # handled via auto_now or something
                (self.item1.pk, 3, None)
            ]
        )
    
    def test_top_extra_update(self):
        modified_time = now()
        self.item4.top(extra_update={'modified':modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list('pk', 'order', 'modified'), [
                (self.item4.pk, 0, None),
                (self.item1.pk, 1, modified_time),
                (self.item2.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be 
                # handled via auto_now or something
                (self.item3.pk, 3, modified_time)
            ]
        )
    
    def test_below_extra_update(self):
        modified_time = now()
        self.item1.below(self.item4, extra_update={'modified':modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list('pk', 'order', 'modified'), [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be 
                # handled via auto_now or something
                (self.item1.pk, 3, None)
            ]
        )
    
    def test_above_extra_update(self):
        modified_time = now()
        self.item4.above(self.item1, extra_update={'modified':modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list('pk', 'order', 'modified'), [
                (self.item4.pk, 0, None),
                (self.item1.pk, 1, modified_time),
                (self.item2.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be 
                # handled via auto_now or something
                (self.item3.pk, 3, modified_time)
            ]
        )
    
    def test_delete_extra_update(self):
        modified_time = now()
        self.item1.delete(extra_update={'modified':modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list('pk', 'order', 'modified'), [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
            ]
        )



class CustomOrderFieldTest(TestCase):
    fixtures = ['test_items.json']

    def assertNames(self, names):
        self.assertEqual(list(enumerate(names)), [(i.sort_order, i.name) for i in CustomOrderFieldModel.objects.all()])

    def test_inserting_new_models(self):
        CustomOrderFieldModel.objects.create(name='Wurble')
        self.assertNames(['1', '2', '3', '4', 'Wurble'])

    def test_up(self):
        CustomOrderFieldModel.objects.get(pk=4).up()
        self.assertNames(['1', '2', '4', '3'])

    def test_up_first(self):
        CustomOrderFieldModel.objects.get(pk=1).up()
        self.assertNames(['1', '2', '3', '4'])

    def test_up_with_gap(self):
        CustomOrderFieldModel.objects.get(pk=3).up()
        self.assertNames(['1', '3', '2', '4'])

    def test_down(self):
        CustomOrderFieldModel.objects.get(pk=1).down()
        self.assertNames(['2', '1', '3', '4'])

    def test_down_last(self):
        CustomOrderFieldModel.objects.get(pk=4).down()
        self.assertNames(['1', '2', '3', '4'])

    def test_down_with_gap(self):
        CustomOrderFieldModel.objects.get(pk=2).down()
        self.assertNames(['1', '3', '2', '4'])

    def test_to(self):
        CustomOrderFieldModel.objects.get(pk=4).to(0)
        self.assertNames(['4', '1', '2', '3'])
        CustomOrderFieldModel.objects.get(pk=4).to(2)
        self.assertNames(['1', '2', '4', '3'])
        CustomOrderFieldModel.objects.get(pk=3).to(1)
        self.assertNames(['1', '3', '2', '4'])

    def test_top(self):
        CustomOrderFieldModel.objects.get(pk=4).top()
        self.assertNames(['4', '1', '2', '3'])
        CustomOrderFieldModel.objects.get(pk=2).top()
        self.assertNames(['2', '4', '1', '3'])

    def test_bottom(self):
        CustomOrderFieldModel.objects.get(pk=1).bottom()
        self.assertNames(['2', '3', '4', '1'])
        CustomOrderFieldModel.objects.get(pk=3).bottom()
        self.assertNames(['2', '4', '1', '3'])

    def test_above(self):
        CustomOrderFieldModel.objects.get(pk=3).above(CustomOrderFieldModel.objects.get(pk=1))
        self.assertNames(['3', '1', '2', '4'])
        CustomOrderFieldModel.objects.get(pk=4).above(CustomOrderFieldModel.objects.get(pk=1))
        self.assertNames(['3', '4', '1', '2'])

    def test_above_self(self):
        CustomOrderFieldModel.objects.get(pk=3).above(CustomOrderFieldModel.objects.get(pk=3))
        self.assertNames(['1', '2', '3', '4'])

    def test_below(self):
        CustomOrderFieldModel.objects.get(pk=1).below(CustomOrderFieldModel.objects.get(pk=3))
        self.assertNames(['2', '3', '1', '4'])
        CustomOrderFieldModel.objects.get(pk=3).below(CustomOrderFieldModel.objects.get(pk=4))
        self.assertNames(['2', '1', '4', '3'])

    def test_below_self(self):
        CustomOrderFieldModel.objects.get(pk=2).below(CustomOrderFieldModel.objects.get(pk=2))
        self.assertNames(['1', '2', '3', '4'])

    def test_delete(self):
        CustomOrderFieldModel.objects.get(pk=2).delete()
        self.assertNames(['1', '3', '4'])
        CustomOrderFieldModel.objects.get(pk=3).up()
        self.assertNames(['3', '1', '4'])


class OrderedModelAdminTest(TestCase):
    def setUp(self):
        user = User.objects.create_superuser("admin", "a@example.com", "admin")
        self.assertTrue(self.client.login(username="admin", password="admin"))
        item1 = Item.objects.create(name='item1')
        item2 = Item.objects.create(name='item2')

    def test_move_up_down_links(self):
        res = self.client.get("/admin/tests/item/")
        self.assertEqual(res.status_code, 200)
        self.assertIn('/admin/tests/item/1/move-up/', str(res.content))
        self.assertIn('/admin/tests/item/1/move-down/', str(res.content))

    def test_move_down(self):
        self.assertEqual(Item.objects.get(name="item1").order, 0)
        self.assertEqual(Item.objects.get(name="item2").order, 1)
        res = self.client.get("/admin/tests/item/1/move-down/")
        self.assertRedirects(res, "/admin/tests/item/")
        self.assertEqual(Item.objects.get(name="item1").order, 1)
        self.assertEqual(Item.objects.get(name="item2").order, 0)

    def test_move_up(self):
        self.assertEqual(Item.objects.get(name="item1").order, 0)
        self.assertEqual(Item.objects.get(name="item2").order, 1)
        res = self.client.get("/admin/tests/item/2/move-up/")
        self.assertRedirects(res, "/admin/tests/item/")
        self.assertEqual(Item.objects.get(name="item1").order, 1)
        self.assertEqual(Item.objects.get(name="item2").order, 0)


class OrderWithRespectToTestsManyToMany(TestCase):
    def setUp(self):
        self.t1 = Topping.objects.create(name='tomatoe')
        self.t2 = Topping.objects.create(name='mozarella')
        self.t3 = Topping.objects.create(name='anchovy')
        self.t4 = Topping.objects.create(name='mushrooms')
        self.t5 = Topping.objects.create(name='ham')
        self.p1 = Pizza.objects.create(name='Napoli') # tomatoe, mozarella, anchovy
        self.p2 = Pizza.objects.create(name='Regina') # tomatoe, mozarella, mushrooms, ham
        # Now put the toppings on the pizza
        self.p1_t1 = PizzaToppingsThroughModel(pizza=self.p1, topping=self.t1)
        self.p1_t1.save()
        self.p1_t2 = PizzaToppingsThroughModel(pizza=self.p1, topping=self.t2)
        self.p1_t2.save()
        self.p1_t3 = PizzaToppingsThroughModel(pizza=self.p1, topping=self.t3)
        self.p1_t3.save()
        self.p2_t1 = PizzaToppingsThroughModel(pizza=self.p2, topping=self.t1)
        self.p2_t1.save()
        self.p2_t2 = PizzaToppingsThroughModel(pizza=self.p2, topping=self.t2)
        self.p2_t2.save()
        self.p2_t3 = PizzaToppingsThroughModel(pizza=self.p2, topping=self.t4)
        self.p2_t3.save()
        self.p2_t4 = PizzaToppingsThroughModel(pizza=self.p2, topping=self.t5)
        self.p2_t4.save()

    def test_saved_order(self):
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t1.topping.pk, 0), (self.p1_t2.topping.pk, 1), (self.p1_t3.topping.pk, 2),
            (self.p2_t1.topping.pk, 0), (self.p2_t2.topping.pk, 1), (self.p2_t3.topping.pk, 2), (self.p2_t4.topping.pk, 3)
        ])

    def test_swap(self):
        with self.assertRaises(ValueError):
            self.p1_t1.swap([self.p2_t1])

    def test_up(self):
        self.p1_t2.up()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t2.topping.pk, 0), (self.p1_t1.topping.pk, 1), (self.p1_t3.topping.pk, 2),
            (self.p2_t1.topping.pk, 0), (self.p2_t2.topping.pk, 1), (self.p2_t3.topping.pk, 2), (self.p2_t4.topping.pk, 3)
        ])

    def test_down(self):
        self.p2_t1.down()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t1.topping.pk, 0), (self.p1_t2.topping.pk, 1), (self.p1_t3.topping.pk, 2),
            (self.p2_t2.topping.pk, 0), (self.p2_t1.topping.pk, 1), (self.p2_t3.topping.pk, 2), (self.p2_t4.topping.pk, 3)
        ])

    def test_to(self):
        self.p2_t1.to(1)
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t1.topping.pk, 0), (self.p1_t2.topping.pk, 1), (self.p1_t3.topping.pk, 2),
            (self.p2_t2.topping.pk, 0), (self.p2_t1.topping.pk, 1), (self.p2_t3.topping.pk, 2), (self.p2_t4.topping.pk, 3)
        ])

    def test_above(self):
        with self.assertRaises(ValueError):
            self.p1_t2.above(self.p2_t1)
        self.p1_t2.above(self.p1_t1)
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t2.topping.pk, 0), (self.p1_t1.topping.pk, 1), (self.p1_t3.topping.pk, 2),
            (self.p2_t1.topping.pk, 0), (self.p2_t2.topping.pk, 1), (self.p2_t3.topping.pk, 2), (self.p2_t4.topping.pk, 3)
        ])

    def test_below(self):
        with self.assertRaises(ValueError):
            self.p2_t1.below(self.p1_t2)
        self.p2_t1.below(self.p2_t2)
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t1.topping.pk, 0), (self.p1_t2.topping.pk, 1), (self.p1_t3.topping.pk, 2),
            (self.p2_t2.topping.pk, 0), (self.p2_t1.topping.pk, 1), (self.p2_t3.topping.pk, 2), (self.p2_t4.topping.pk, 3)
        ])

    def test_top(self):
        self.p1_t3.top()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t3.topping.pk, 0), (self.p1_t1.topping.pk, 1), (self.p1_t2.topping.pk, 2),
            (self.p2_t1.topping.pk, 0), (self.p2_t2.topping.pk, 1), (self.p2_t3.topping.pk, 2), (self.p2_t4.topping.pk, 3)
        ])

    def test_bottom(self):
        self.p2_t1.bottom()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list('topping__pk', 'order'), [
            (self.p1_t1.topping.pk, 0), (self.p1_t2.topping.pk, 1), (self.p1_t3.topping.pk, 2),
            (self.p2_t2.topping.pk, 0), (self.p2_t3.topping.pk, 1), (self.p2_t4.topping.pk, 2), (self.p2_t1.topping.pk, 3)
        ])

class MultiOrderWithRespectToTests(TestCase):
    def setUp(self):
        q1 = Question.objects.create()
        q2 = Question.objects.create()
        u1 = TestUser.objects.create()
        u2 = TestUser.objects.create()
        self.q1_u1_a1 = q1.answers.create(user=u1)
        self.q2_u1_a1 = q2.answers.create(user=u1)
        self.q1_u1_a2 = q1.answers.create(user=u1)
        self.q2_u1_a2 = q2.answers.create(user=u1)
        self.q1_u2_a1 = q1.answers.create(user=u2)
        self.q2_u2_a1 = q2.answers.create(user=u2)
        self.q1_u2_a2 = q1.answers.create(user=u2)
        self.q2_u2_a2 = q2.answers.create(user=u2)

    def test_saved_order(self):
        self.assertSequenceEqual(
            Answer.objects.values_list('pk', 'order'), [
            (self.q1_u1_a1.pk, 0), (self.q1_u1_a2.pk, 1),
            (self.q1_u2_a1.pk, 0), (self.q1_u2_a2.pk, 1),
            (self.q2_u1_a1.pk, 0), (self.q2_u1_a2.pk, 1),
            (self.q2_u2_a1.pk, 0), (self.q2_u2_a2.pk, 1)
        ])

    def test_swap_fails(self):
        with self.assertRaises(ValueError):
            self.q1_u1_a1.swap([self.q2_u1_a2])
