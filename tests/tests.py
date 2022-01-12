import uuid
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils.timezone import now
from django.test import TestCase
from django import VERSION

from tests.models import (
    Answer,
    Item,
    Question,
    CustomItem,
    CustomOrderFieldModel,
    CustomPKGroupItem,
    CustomPKGroup,
    Pizza,
    Topping,
    PizzaToppingsThroughModel,
    OpenQuestion,
    MultipleChoiceQuestion,
    ItemGroup,
    GroupedItem,
    TestUser,
)


class OrderGenerationTests(TestCase):
    def test_second_order_generation(self):
        first_item = Item.objects.create()
        self.assertEqual(first_item.order, 0)
        second_item = Item.objects.create()
        self.assertEqual(second_item.order, 1)


class ModelTestCase(TestCase):
    fixtures = ["test_items.json"]

    def assertNames(self, names):
        self.assertEqual(
            list(enumerate(names)), [(i.order, i.name) for i in Item.objects.all()]
        )

    def test_inserting_new_models(self):
        Item.objects.create(name="Wurble")
        self.assertNames(["1", "2", "3", "4", "Wurble"])

    def test_previous(self):
        self.assertEqual(Item.objects.get(pk=4).previous(), Item.objects.get(pk=3))

    def test_previous_first(self):
        self.assertEqual(Item.objects.get(pk=1).previous(), None)

    def test_previous_with_gap(self):
        self.assertEqual(Item.objects.get(pk=3).previous(), Item.objects.get(pk=2))

    def test_next(self):
        self.assertEqual(Item.objects.get(pk=1).next(), Item.objects.get(pk=2))

    def test_next_last(self):
        self.assertEqual(Item.objects.get(pk=4).next(), None)

    def test_next_with_gap(self):
        self.assertEqual(Item.objects.get(pk=2).next(), Item.objects.get(pk=3))

    def test_up(self):
        Item.objects.get(pk=4).up()
        self.assertNames(["1", "2", "4", "3"])

    def test_up_first(self):
        Item.objects.get(pk=1).up()
        self.assertNames(["1", "2", "3", "4"])

    def test_up_with_gap(self):
        Item.objects.get(pk=3).up()
        self.assertNames(["1", "3", "2", "4"])

    def test_down(self):
        Item.objects.get(pk=1).down()
        self.assertNames(["2", "1", "3", "4"])

    def test_down_last(self):
        Item.objects.get(pk=4).down()
        self.assertNames(["1", "2", "3", "4"])

    def test_down_with_gap(self):
        Item.objects.get(pk=2).down()
        self.assertNames(["1", "3", "2", "4"])

    def test_to(self):
        Item.objects.get(pk=4).to(0)
        self.assertNames(["4", "1", "2", "3"])
        Item.objects.get(pk=4).to(2)
        self.assertNames(["1", "2", "4", "3"])
        Item.objects.get(pk=3).to(1)
        self.assertNames(["1", "3", "2", "4"])

    def test_to_not_int(self):
        with self.assertRaises(TypeError):
            Item.objects.get(pk=4).to("1")

    def test_top(self):
        Item.objects.get(pk=4).top()
        self.assertNames(["4", "1", "2", "3"])
        Item.objects.get(pk=2).top()
        self.assertNames(["2", "4", "1", "3"])

    def test_bottom(self):
        Item.objects.get(pk=1).bottom()
        self.assertNames(["2", "3", "4", "1"])
        Item.objects.get(pk=3).bottom()
        self.assertNames(["2", "4", "1", "3"])

    def test_above(self):
        Item.objects.get(pk=3).above(Item.objects.get(pk=1))
        self.assertNames(["3", "1", "2", "4"])
        Item.objects.get(pk=4).above(Item.objects.get(pk=1))
        self.assertNames(["3", "4", "1", "2"])

    def test_above_self(self):
        Item.objects.get(pk=3).above(Item.objects.get(pk=3))
        self.assertNames(["1", "2", "3", "4"])

    def test_below(self):
        Item.objects.get(pk=1).below(Item.objects.get(pk=3))
        self.assertNames(["2", "3", "1", "4"])
        Item.objects.get(pk=3).below(Item.objects.get(pk=4))
        self.assertNames(["2", "1", "4", "3"])

    def test_below_self(self):
        Item.objects.get(pk=2).below(Item.objects.get(pk=2))
        self.assertNames(["1", "2", "3", "4"])

    def test_delete(self):
        Item.objects.get(pk=2).delete()
        self.assertNames(["1", "3", "4"])
        Item.objects.get(pk=3).up()
        self.assertNames(["3", "1", "4"])


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
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a1.pk, 0),
                (self.q1_a2.pk, 1),
                (self.q2_a1.pk, 0),
                (self.q2_a2.pk, 1),
            ],
        )

    def test_previous(self):
        self.assertEqual(self.q1_a2.previous(), self.q1_a1)

    def test_previous_first(self):
        self.assertEqual(self.q2_a1.previous(), None)

    def test_next(self):
        self.assertEqual(self.q2_a1.next(), self.q2_a2)

    def test_next_last(self):
        self.assertEqual(self.q1_a2.next(), None)

    def test_swap(self):
        with self.assertRaises(ValueError):
            self.q1_a1.swap(self.q2_a1)

        self.q1_a1.swap(self.q1_a2)
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a2.pk, 0),
                (self.q1_a1.pk, 1),
                (self.q2_a1.pk, 0),
                (self.q2_a2.pk, 1),
            ],
        )

    def test_up(self):
        self.q1_a2.up()
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a2.pk, 0),
                (self.q1_a1.pk, 1),
                (self.q2_a1.pk, 0),
                (self.q2_a2.pk, 1),
            ],
        )

    def test_down(self):
        self.q2_a1.down()
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a1.pk, 0),
                (self.q1_a2.pk, 1),
                (self.q2_a2.pk, 0),
                (self.q2_a1.pk, 1),
            ],
        )

    def test_to(self):
        self.q2_a1.to(1)
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a1.pk, 0),
                (self.q1_a2.pk, 1),
                (self.q2_a2.pk, 0),
                (self.q2_a1.pk, 1),
            ],
        )

    def test_above(self):
        with self.assertRaises(ValueError):
            self.q1_a2.above(self.q2_a1)
        self.q1_a2.above(self.q1_a1)
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a2.pk, 0),
                (self.q1_a1.pk, 1),
                (self.q2_a1.pk, 0),
                (self.q2_a2.pk, 1),
            ],
        )

    def test_below(self):
        with self.assertRaises(ValueError):
            self.q2_a1.below(self.q1_a2)
        self.q2_a1.below(self.q2_a2)
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a1.pk, 0),
                (self.q1_a2.pk, 1),
                (self.q2_a2.pk, 0),
                (self.q2_a1.pk, 1),
            ],
        )

    def test_top(self):
        self.q1_a2.top()
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a2.pk, 0),
                (self.q1_a1.pk, 1),
                (self.q2_a1.pk, 0),
                (self.q2_a2.pk, 1),
            ],
        )

    def test_bottom(self):
        self.q2_a1.bottom()
        self.assertSequenceEqual(
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_a1.pk, 0),
                (self.q1_a2.pk, 1),
                (self.q2_a2.pk, 0),
                (self.q2_a1.pk, 1),
            ],
        )


class CustomPKTest(TestCase):
    def setUp(self):
        self.item1 = CustomItem.objects.create(pkid=str(uuid.uuid4()), name="1")
        self.item2 = CustomItem.objects.create(pkid=str(uuid.uuid4()), name="2")
        self.item3 = CustomItem.objects.create(pkid=str(uuid.uuid4()), name="3")
        self.item4 = CustomItem.objects.create(pkid=str(uuid.uuid4()), name="4")

    def test_saved_order(self):
        self.assertSequenceEqual(
            CustomItem.objects.values_list("pk", "order"),
            [
                (self.item1.pk, 0),
                (self.item2.pk, 1),
                (self.item3.pk, 2),
                (self.item4.pk, 3),
            ],
        )

    def test_order_to_extra_update(self):
        modified_time = now()
        self.item1.to(3, extra_update={"modified": modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list("pk", "order", "modified"),
            [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be
                # handled via auto_now or something
                (self.item1.pk, 3, None),
            ],
        )

    def test_bottom_extra_update(self):
        modified_time = now()
        self.item1.bottom(extra_update={"modified": modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list("pk", "order", "modified"),
            [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be
                # handled via auto_now or something
                (self.item1.pk, 3, None),
            ],
        )

    def test_top_extra_update(self):
        modified_time = now()
        self.item4.top(extra_update={"modified": modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list("pk", "order", "modified"),
            [
                (self.item4.pk, 0, None),
                (self.item1.pk, 1, modified_time),
                (self.item2.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be
                # handled via auto_now or something
                (self.item3.pk, 3, modified_time),
            ],
        )

    def test_below_extra_update(self):
        modified_time = now()
        self.item1.below(self.item4, extra_update={"modified": modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list("pk", "order", "modified"),
            [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be
                # handled via auto_now or something
                (self.item1.pk, 3, None),
            ],
        )

    def test_above_extra_update(self):
        modified_time = now()
        self.item4.above(self.item1, extra_update={"modified": modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list("pk", "order", "modified"),
            [
                (self.item4.pk, 0, None),
                (self.item1.pk, 1, modified_time),
                (self.item2.pk, 2, modified_time),
                # This one is the primary item being operated on and modified would be
                # handled via auto_now or something
                (self.item3.pk, 3, modified_time),
            ],
        )

    def test_delete_extra_update(self):
        modified_time = now()
        self.item1.delete(extra_update={"modified": modified_time})
        self.assertSequenceEqual(
            CustomItem.objects.values_list("pk", "order", "modified"),
            [
                (self.item2.pk, 0, modified_time),
                (self.item3.pk, 1, modified_time),
                (self.item4.pk, 2, modified_time),
            ],
        )


class CustomOrderFieldTest(TestCase):
    fixtures = ["test_items.json"]

    def assertNames(self, names):
        self.assertEqual(
            list(enumerate(names)),
            [(i.sort_order, i.name) for i in CustomOrderFieldModel.objects.all()],
        )

    def test_inserting_new_models(self):
        CustomOrderFieldModel.objects.create(name="Wurble")
        self.assertNames(["1", "2", "3", "4", "Wurble"])

    def test_previous(self):
        self.assertEqual(
            CustomOrderFieldModel.objects.get(pk=4).previous(),
            CustomOrderFieldModel.objects.get(pk=3),
        )

    def test_previous_first(self):
        self.assertEqual(CustomOrderFieldModel.objects.get(pk=1).previous(), None)

    def test_previous_with_gap(self):
        self.assertEqual(
            CustomOrderFieldModel.objects.get(pk=3).previous(),
            CustomOrderFieldModel.objects.get(pk=2),
        )

    def test_next(self):
        self.assertEqual(
            CustomOrderFieldModel.objects.get(pk=1).next(),
            CustomOrderFieldModel.objects.get(pk=2),
        )

    def test_next_last(self):
        self.assertEqual(CustomOrderFieldModel.objects.get(pk=4).next(), None)

    def test_next_with_gap(self):
        self.assertEqual(
            CustomOrderFieldModel.objects.get(pk=2).next(),
            CustomOrderFieldModel.objects.get(pk=3),
        )

    def test_up(self):
        CustomOrderFieldModel.objects.get(pk=4).up()
        self.assertNames(["1", "2", "4", "3"])

    def test_up_first(self):
        CustomOrderFieldModel.objects.get(pk=1).up()
        self.assertNames(["1", "2", "3", "4"])

    def test_up_with_gap(self):
        CustomOrderFieldModel.objects.get(pk=3).up()
        self.assertNames(["1", "3", "2", "4"])

    def test_down(self):
        CustomOrderFieldModel.objects.get(pk=1).down()
        self.assertNames(["2", "1", "3", "4"])

    def test_down_last(self):
        CustomOrderFieldModel.objects.get(pk=4).down()
        self.assertNames(["1", "2", "3", "4"])

    def test_down_with_gap(self):
        CustomOrderFieldModel.objects.get(pk=2).down()
        self.assertNames(["1", "3", "2", "4"])

    def test_to(self):
        CustomOrderFieldModel.objects.get(pk=4).to(0)
        self.assertNames(["4", "1", "2", "3"])
        CustomOrderFieldModel.objects.get(pk=4).to(2)
        self.assertNames(["1", "2", "4", "3"])
        CustomOrderFieldModel.objects.get(pk=3).to(1)
        self.assertNames(["1", "3", "2", "4"])

    def test_top(self):
        CustomOrderFieldModel.objects.get(pk=4).top()
        self.assertNames(["4", "1", "2", "3"])
        CustomOrderFieldModel.objects.get(pk=2).top()
        self.assertNames(["2", "4", "1", "3"])

    def test_bottom(self):
        CustomOrderFieldModel.objects.get(pk=1).bottom()
        self.assertNames(["2", "3", "4", "1"])
        CustomOrderFieldModel.objects.get(pk=3).bottom()
        self.assertNames(["2", "4", "1", "3"])

    def test_above(self):
        CustomOrderFieldModel.objects.get(pk=3).above(
            CustomOrderFieldModel.objects.get(pk=1)
        )
        self.assertNames(["3", "1", "2", "4"])
        CustomOrderFieldModel.objects.get(pk=4).above(
            CustomOrderFieldModel.objects.get(pk=1)
        )
        self.assertNames(["3", "4", "1", "2"])

    def test_above_self(self):
        CustomOrderFieldModel.objects.get(pk=3).above(
            CustomOrderFieldModel.objects.get(pk=3)
        )
        self.assertNames(["1", "2", "3", "4"])

    def test_below(self):
        CustomOrderFieldModel.objects.get(pk=1).below(
            CustomOrderFieldModel.objects.get(pk=3)
        )
        self.assertNames(["2", "3", "1", "4"])
        CustomOrderFieldModel.objects.get(pk=3).below(
            CustomOrderFieldModel.objects.get(pk=4)
        )
        self.assertNames(["2", "1", "4", "3"])

    def test_below_self(self):
        CustomOrderFieldModel.objects.get(pk=2).below(
            CustomOrderFieldModel.objects.get(pk=2)
        )
        self.assertNames(["1", "2", "3", "4"])

    def test_delete(self):
        CustomOrderFieldModel.objects.get(pk=2).delete()
        self.assertNames(["1", "3", "4"])
        CustomOrderFieldModel.objects.get(pk=3).up()
        self.assertNames(["3", "1", "4"])


class OrderedModelAdminTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("admin", "a@example.com", "admin")
        self.assertTrue(self.client.login(username="admin", password="admin"))
        Item.objects.create(name="item1")
        Item.objects.create(name="item2")
        Item.objects.create(name="item3")

        self.ham = Topping.objects.create(name="Ham")
        self.pineapple = Topping.objects.create(name="Pineapple")

        self.pizza = Pizza.objects.create(name="Hawaiian Pizza")
        self.pizza_to_ham = PizzaToppingsThroughModel.objects.create(
            pizza=self.pizza, topping=self.ham
        )
        self.pizza_to_pineapple = PizzaToppingsThroughModel.objects.create(
            pizza=self.pizza, topping=self.pineapple
        )

    def test_move_links(self):
        res = self.client.get("/admin/tests/item/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("/admin/tests/item/1/move-up/", str(res.content))
        self.assertIn("/admin/tests/item/1/move-down/", str(res.content))
        self.assertIn("/admin/tests/item/1/move-top/", str(res.content))
        self.assertIn("/admin/tests/item/1/move-bottom/", str(res.content))

    def test_move_invalid_direction(self):
        res = self.client.get("/admin/tests/item/1/move-middle/")
        self.assertEqual(res.status_code, 404)

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

    def test_move_top(self):
        self.assertEqual(Item.objects.get(name="item1").order, 0)
        self.assertEqual(Item.objects.get(name="item2").order, 1)
        self.assertEqual(Item.objects.get(name="item3").order, 2)
        res = self.client.get("/admin/tests/item/3/move-top/")
        self.assertRedirects(res, "/admin/tests/item/")
        self.assertEqual(Item.objects.get(name="item1").order, 1)
        self.assertEqual(Item.objects.get(name="item2").order, 2)
        self.assertEqual(Item.objects.get(name="item3").order, 0)

    def test_move_bottom(self):
        self.assertEqual(Item.objects.get(name="item1").order, 0)
        self.assertEqual(Item.objects.get(name="item2").order, 1)
        self.assertEqual(Item.objects.get(name="item3").order, 2)
        res = self.client.get("/admin/tests/item/1/move-bottom/")
        self.assertRedirects(res, "/admin/tests/item/")
        self.assertEqual(Item.objects.get(name="item1").order, 2)
        self.assertEqual(Item.objects.get(name="item2").order, 0)
        self.assertEqual(Item.objects.get(name="item3").order, 1)

    def test_move_up_down_links_ordered_inline(self):
        # model list
        res = self.client.get("/admin/tests/pizza/")
        self.assertContains(
            res, text="/admin/tests/pizza/{}/change/".format(self.pizza.id)
        )

        # model page including inlines
        res = self.client.get("/admin/tests/pizza/{}/change/".format(self.pizza.id))
        self.assertContains(
            res,
            text='<a href="/admin/tests/pizza/{}/pizzatoppingsthroughmodel/{}/move-up/">'.format(
                self.pizza.id, self.pizza_to_ham.id
            ),
        )
        self.assertContains(
            res,
            text='<a href="/admin/tests/pizza/{}/pizzatoppingsthroughmodel/{}/move-up/">'.format(
                self.pizza.id, self.pizza_to_pineapple.id
            ),
        )

        # click the move-up link
        self.assertEqual(self.pizza_to_ham.order, 0)
        self.assertEqual(self.pizza_to_pineapple.order, 1)
        res = self.client.get(
            "/admin/tests/pizza/{}/pizzatoppingsthroughmodel/{}/move-up/".format(
                self.pizza.id, self.pizza_to_pineapple.id
            ),
            follow=True,
        )
        self.pizza_to_ham.refresh_from_db()
        self.pizza_to_pineapple.refresh_from_db()
        self.assertEqual(self.pizza_to_ham.order, 1)
        self.assertEqual(self.pizza_to_pineapple.order, 0)
        self.assertEqual(res.status_code, 200)

    def test_move_up_down_proxy_stacked_inline(self):
        res = self.client.get("/admin/tests/pizzaproxy/")
        self.assertContains(
            res, text="/admin/tests/pizzaproxy/{}/change/".format(self.pizza.id)
        )

        res = self.client.get(
            "/admin/tests/pizzaproxy/{}/change/".format(self.pizza.id)
        )
        self.assertContains(
            res,
            text='<a href="/admin/tests/pizzaproxy/{}/pizzatoppingsthroughmodel/{}/move-up/">'.format(
                self.pizza.id, self.pizza_to_ham.id
            ),
        )


class OrderWithRespectToTestsManyToMany(TestCase):
    def setUp(self):
        self.t1 = Topping.objects.create(name="tomatoe")
        self.t2 = Topping.objects.create(name="mozarella")
        self.t3 = Topping.objects.create(name="anchovy")
        self.t4 = Topping.objects.create(name="mushrooms")
        self.t5 = Topping.objects.create(name="ham")
        self.p1 = Pizza.objects.create(name="Napoli")  # tomatoe, mozarella, anchovy
        self.p2 = Pizza.objects.create(
            name="Regina"
        )  # tomatoe, mozarella, mushrooms, ham
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
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t1.topping.pk, 0),
                (self.p1_t2.topping.pk, 1),
                (self.p1_t3.topping.pk, 2),
                (self.p2_t1.topping.pk, 0),
                (self.p2_t2.topping.pk, 1),
                (self.p2_t3.topping.pk, 2),
                (self.p2_t4.topping.pk, 3),
            ],
        )

    def test_swap(self):
        with self.assertRaises(ValueError):
            self.p1_t1.swap(self.p2_t1)

    def test_previous(self):
        self.assertEqual(self.p1_t2.previous(), self.p1_t1)

    def test_previous_first(self):
        self.assertEqual(self.p2_t1.previous(), None)

    def test_down(self):
        self.assertEqual(self.p2_t1.next(), self.p2_t2)

    def test_down_last(self):
        self.assertEqual(self.p1_t3.next(), None)

    def test_up(self):
        self.p1_t2.up()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t2.topping.pk, 0),
                (self.p1_t1.topping.pk, 1),
                (self.p1_t3.topping.pk, 2),
                (self.p2_t1.topping.pk, 0),
                (self.p2_t2.topping.pk, 1),
                (self.p2_t3.topping.pk, 2),
                (self.p2_t4.topping.pk, 3),
            ],
        )

    def test_down(self):
        self.p2_t1.down()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t1.topping.pk, 0),
                (self.p1_t2.topping.pk, 1),
                (self.p1_t3.topping.pk, 2),
                (self.p2_t2.topping.pk, 0),
                (self.p2_t1.topping.pk, 1),
                (self.p2_t3.topping.pk, 2),
                (self.p2_t4.topping.pk, 3),
            ],
        )

    def test_to(self):
        self.p2_t1.to(1)
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t1.topping.pk, 0),
                (self.p1_t2.topping.pk, 1),
                (self.p1_t3.topping.pk, 2),
                (self.p2_t2.topping.pk, 0),
                (self.p2_t1.topping.pk, 1),
                (self.p2_t3.topping.pk, 2),
                (self.p2_t4.topping.pk, 3),
            ],
        )

    def test_above(self):
        with self.assertRaises(ValueError):
            self.p1_t2.above(self.p2_t1)
        self.p1_t2.above(self.p1_t1)
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t2.topping.pk, 0),
                (self.p1_t1.topping.pk, 1),
                (self.p1_t3.topping.pk, 2),
                (self.p2_t1.topping.pk, 0),
                (self.p2_t2.topping.pk, 1),
                (self.p2_t3.topping.pk, 2),
                (self.p2_t4.topping.pk, 3),
            ],
        )

    def test_below(self):
        with self.assertRaises(ValueError):
            self.p2_t1.below(self.p1_t2)
        self.p2_t1.below(self.p2_t2)
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t1.topping.pk, 0),
                (self.p1_t2.topping.pk, 1),
                (self.p1_t3.topping.pk, 2),
                (self.p2_t2.topping.pk, 0),
                (self.p2_t1.topping.pk, 1),
                (self.p2_t3.topping.pk, 2),
                (self.p2_t4.topping.pk, 3),
            ],
        )

    def test_top(self):
        self.p1_t3.top()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t3.topping.pk, 0),
                (self.p1_t1.topping.pk, 1),
                (self.p1_t2.topping.pk, 2),
                (self.p2_t1.topping.pk, 0),
                (self.p2_t2.topping.pk, 1),
                (self.p2_t3.topping.pk, 2),
                (self.p2_t4.topping.pk, 3),
            ],
        )

    def test_bottom(self):
        self.p2_t1.bottom()
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.values_list("topping__pk", "order"),
            [
                (self.p1_t1.topping.pk, 0),
                (self.p1_t2.topping.pk, 1),
                (self.p1_t3.topping.pk, 2),
                (self.p2_t2.topping.pk, 0),
                (self.p2_t3.topping.pk, 1),
                (self.p2_t4.topping.pk, 2),
                (self.p2_t1.topping.pk, 3),
            ],
        )


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
            Answer.objects.values_list("pk", "order"),
            [
                (self.q1_u1_a1.pk, 0),
                (self.q1_u1_a2.pk, 1),
                (self.q1_u2_a1.pk, 0),
                (self.q1_u2_a2.pk, 1),
                (self.q2_u1_a1.pk, 0),
                (self.q2_u1_a2.pk, 1),
                (self.q2_u2_a1.pk, 0),
                (self.q2_u2_a2.pk, 1),
            ],
        )

    def test_swap_fails(self):
        with self.assertRaises(ValueError):
            self.q1_u1_a1.swap(self.q2_u1_a2)


class OrderWithRespectToRelatedModelFieldTests(TestCase):
    def setUp(self):
        self.u1 = TestUser.objects.create()
        self.u2 = TestUser.objects.create()
        self.u1_g1 = self.u1.item_groups.create()
        self.u2_g1 = self.u2.item_groups.create()
        self.u2_g2 = self.u2.item_groups.create()
        self.u1_g2 = self.u1.item_groups.create()
        self.u2_g2_i1 = self.u2_g2.items.create()
        self.u2_g1_i1 = self.u2_g1.items.create()
        self.u1_g1_i1 = self.u1_g1.items.create()
        self.u1_g2_i1 = self.u1_g2.items.create()

    def test_saved_order(self):
        self.assertSequenceEqual(
            GroupedItem.objects.filter(group__user=self.u1).values_list("pk", "order"),
            [(self.u1_g1_i1.pk, 0), (self.u1_g2_i1.pk, 1)],
        )

        self.assertSequenceEqual(
            GroupedItem.objects.filter(group__user=self.u2).values_list("pk", "order"),
            [(self.u2_g2_i1.pk, 0), (self.u2_g1_i1.pk, 1)],
        )

    def test_swap(self):
        i2 = self.u1_g1.items.create()
        self.assertSequenceEqual(
            GroupedItem.objects.filter(group__user=self.u1).values_list("pk", "order"),
            [(self.u1_g1_i1.pk, 0), (self.u1_g2_i1.pk, 1), (i2.pk, 2)],
        )

        i2.swap(self.u1_g1_i1)
        self.assertSequenceEqual(
            GroupedItem.objects.filter(group__user=self.u1).values_list("pk", "order"),
            [(i2.pk, 0), (self.u1_g2_i1.pk, 1), (self.u1_g1_i1.pk, 2)],
        )

    def test_swap_fails_between_users(self):
        with self.assertRaises(ValueError):
            self.u1_g1_i1.swap(self.u2_g1_i1)

    def test_above_between_groups(self):
        i2 = self.u1_g2.items.create()
        i2.above(self.u1_g1_i1)
        self.assertSequenceEqual(
            GroupedItem.objects.filter(group__user=self.u1).values_list("pk", "order"),
            [(i2.pk, 0), (self.u1_g1_i1.pk, 1), (self.u1_g2_i1.pk, 2)],
        )


class PolymorphicOrderGenerationTests(TestCase):
    def test_order_of_baselist(self):
        o1 = OpenQuestion.objects.create()
        self.assertEqual(o1.order, 0)
        o1.save()
        m1 = MultipleChoiceQuestion.objects.create()
        self.assertEqual(m1.order, 1)
        m1.save()
        m2 = MultipleChoiceQuestion.objects.create()
        self.assertEqual(m2.order, 2)
        m2.save()
        o2 = OpenQuestion.objects.create()
        self.assertEqual(o2.order, 3)
        o2.save()

        m2.up()
        self.assertEqual(m2.order, 1)
        m1.refresh_from_db()
        self.assertEqual(m1.order, 2)
        o2.up()
        self.assertEqual(o2.order, 2)
        m1.refresh_from_db()
        self.assertEqual(m1.order, 3)

    def test_returns_polymorphic(self):
        o1 = OpenQuestion.objects.create()
        self.assertIsInstance(o1, OpenQuestion)


class BulkCreateTests(TestCase):
    def test(self):
        Item.objects.bulk_create([Item(name="1")])
        self.assertEqual(Item.objects.get(name="1").order, 0)

    def test_multiple(self):
        Item.objects.bulk_create([Item(name="1"), Item(name="2")])
        self.assertEqual(Item.objects.get(name="1").order, 0)
        self.assertEqual(Item.objects.get(name="2").order, 1)

    def test_with_existing(self):
        Item.objects.create()
        Item.objects.bulk_create([Item(name="1")])
        self.assertEqual(Item.objects.get(name="1").order, 1)

    def test_with_multiple_existing(self):
        Item.objects.create()
        Item.objects.create()
        Item.objects.bulk_create([Item(name="1")])
        self.assertEqual(Item.objects.get(name="1").order, 2)

    def test_order_field_name(self):
        CustomOrderFieldModel.objects.bulk_create([CustomOrderFieldModel(name="1")])
        self.assertEqual(CustomOrderFieldModel.objects.get(name="1").sort_order, 0)

    def test_order_with_respect_to(self):
        hawaiian_pizza = Pizza.objects.create(name="Hawaiian Pizza")
        napoli_pizza = Pizza.objects.create(name="Napoli")
        topping = Topping.objects.create(name="mozarella")
        PizzaToppingsThroughModel.objects.create(pizza=napoli_pizza, topping=topping)
        PizzaToppingsThroughModel.objects.bulk_create(
            [PizzaToppingsThroughModel(pizza=hawaiian_pizza, topping=topping)]
        )
        self.assertEqual(
            PizzaToppingsThroughModel.objects.get(pizza=hawaiian_pizza).order, 0
        )

    def test_order_with_respect_to_multiple(self):
        hawaiian_pizza = Pizza.objects.create(name="Hawaiian Pizza")
        napoli_pizza = Pizza.objects.create(name="Napoli")
        mozarella = Topping.objects.create(name="mozarella")
        pineapple = Topping.objects.create(name="Pineapple")
        PizzaToppingsThroughModel.objects.create(pizza=napoli_pizza, topping=mozarella)
        PizzaToppingsThroughModel.objects.bulk_create(
            [
                PizzaToppingsThroughModel(pizza=hawaiian_pizza, topping=mozarella),
                PizzaToppingsThroughModel(pizza=hawaiian_pizza, topping=pineapple),
            ]
        )
        self.assertSequenceEqual(
            PizzaToppingsThroughModel.objects.filter(pizza=hawaiian_pizza).values_list(
                "order", flat=True
            ),
            [0, 1],
        )


class OrderedModelAdminWithCustomPKInlineTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("admin", "a@example.com", "admin")
        self.assertTrue(self.client.login(username="admin", password="admin"))
        group = CustomPKGroup.objects.create(name="g1")
        CustomPKGroupItem.objects.create(name="g1 i1", group=group)
        CustomPKGroupItem.objects.create(name="g1 i2", group=group)
        group = CustomPKGroup.objects.create(name="g2")
        CustomPKGroupItem.objects.create(name="g2 i1", group=group)

    def test_move_links(self):
        res = self.client.get("/admin/tests/custompkgroup/1/change", follow=True)
        self.assertContains(res, text="CustomPKGroupItem object (g1 i1)")
        self.assertContains(res, text="CustomPKGroupItem object (g1 i2)")

        # Check for the inline column header
        # see Django release notes https://docs.djangoproject.com/en/dev/releases/2.2/#django-contrib-admin
        # What’s new in Django 2.2 > Minor features > django.contrib.admin > Addd a CSS class to the column headers of TabularInline
        if VERSION >= (2, 2):
            self.assertContains(
                res, text='<th class="column-move_up_down_links">Move</th>', html=True
            )
        else:
            self.assertContains(
                res, text="<th>Move</th>", html=True
            )  # pragma: no cover

        # Check move up/down links
        self.assertContains(
            res,
            text='<a href="/admin/tests/custompkgroup/1/custompkgroupitem/g1%20i1/move-up/">',
        )
        self.assertContains(
            res,
            text='<a href="/admin/tests/custompkgroup/1/custompkgroupitem/g1%20i1/move-down/">',
        )


class ReorderModelTestCase(TestCase):
    fixtures = ["test_items.json"]

    def test_reorder_with_no_respect_to(self):
        """
        Test that 'reorder_model' changes the order of OpenQuestions
        when they overlap.
        """
        OpenQuestion.objects.create(order=0)
        OpenQuestion.objects.create(order=0)
        out = StringIO()
        call_command("reorder_model", "tests.OpenQuestion", verbosity=1, stdout=out)

        self.assertSequenceEqual(
            OpenQuestion.objects.values_list("order", flat=True).order_by("order"),
            [0, 1],
        )
        self.assertIn(
            "changing order of tests.OpenQuestion (2) from 0 to 1", out.getvalue()
        )

    def test_reorder_with_respect_to(self):
        """
        Test that when 'with_respect_to' is used 'reorder_model' changes to
        values of the 'order' field to unique values.
        """
        user1 = TestUser.objects.create()
        group1 = ItemGroup.objects.create(user=user1)

        GroupedItem.objects.create(group=group1, order=0)
        GroupedItem.objects.create(group=group1, order=1)
        GroupedItem.objects.create(group=group1, order=1)
        GroupedItem.objects.create(group=group1, order=3)
        GroupedItem.objects.create(group=group1, order=4)

        user2 = TestUser.objects.create()
        group2 = ItemGroup.objects.create(user=user2)

        GroupedItem.objects.create(group=group2)
        GroupedItem.objects.create(group=group2)
        GroupedItem.objects.create(group=group2)

        out = StringIO()
        call_command("reorder_model", "tests.GroupedItem", verbosity=1, stdout=out)

        self.assertSequenceEqual(
            GroupedItem.objects.filter(group=group1)
            .values_list("order", flat=True)
            .order_by("order"),
            [0, 1, 2, 3, 4],
        )

        self.assertSequenceEqual(
            GroupedItem.objects.filter(group=group2)
            .values_list("order", flat=True)
            .order_by("order"),
            [0, 1, 2],
        )

        self.assertEqual(
            "changing order of tests.GroupedItem (3) from 1 to 2\n", out.getvalue()
        )

    def test_reorder_with_custom_order_field(self):
        """
        Test that 'reorder_model' changes the order of OpenQuestions
        when they overlap.
        """
        out = StringIO()
        CustomOrderFieldModel.objects.create(name="5", sort_order=0)
        call_command(
            "reorder_model", "tests.CustomOrderFieldModel", verbosity=1, stdout=out
        )
        self.assertSequenceEqual(
            CustomOrderFieldModel.objects.values_list("sort_order", flat=True).order_by(
                "sort_order"
            ),
            [0, 1, 2, 3, 4],
        )
        self.assertIn(
            "changing order of tests.CustomOrderFieldModel (5) from 0 to 1",
            out.getvalue(),
        )

    def test_shows_alternatives(self):
        out = StringIO()
        call_command("reorder_model", "test.Missing", verbosity=1, stdout=out)
        self.assertIn("Model 'test.Missing' is not an ordered model", out.getvalue())
        self.assertIn("tests.BaseQuestion", out.getvalue())

        out = StringIO()
        call_command("reorder_model", verbosity=1, stdout=out)
        self.assertIn("tests.BaseQuestion", out.getvalue())

    def test_delete_bypass(self):
        OpenQuestion.objects.create(answer="1", order=0)
        OpenQuestion.objects.create(answer="2", order=1)
        OpenQuestion.objects.create(answer="3", order=2)
        OpenQuestion.objects.create(answer="4", order=3)

        # bypass our OrderedModel delete logic to leave a hole in ordering
        OpenQuestion.objects.filter(answer="3").delete()

        self.assertEqual([0, 1, 3], [i.order for i in OpenQuestion.objects.all()])
        self.assertEqual(
            ["1", "2", "4"], [i.answer for i in OpenQuestion.objects.all()]
        )

        # repair
        out = StringIO()
        call_command("reorder_model", "tests.OpenQuestion", stdout=out)

        self.assertEqual([0, 1, 2], [i.order for i in OpenQuestion.objects.all()])
        self.assertEqual(
            ["1", "2", "4"], [i.answer for i in OpenQuestion.objects.all()]
        )

        self.assertEqual(
            "changing order of tests.OpenQuestion (4) from 3 to 2\n", out.getvalue()
        )
