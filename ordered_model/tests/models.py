from django.db import models
from ordered_model.models import OrderedModel

class Item(OrderedModel):
    name = models.CharField(max_length=100)
