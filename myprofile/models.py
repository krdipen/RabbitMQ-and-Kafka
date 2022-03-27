from django.db import models

class Inventory(models.Model):
    productname = models.CharField(max_length=250, null=True, blank=True)
    unitcost = models.FloatField(null=True, blank=True)
    itemcount = models.PositiveIntegerField(null=True, blank=True)
    variant = models.CharField(max_length=1, null=True, blank=True)

class Orders(models.Model):
    customername = models.CharField(max_length=250, null=True, blank=True)
    item1id = models.IntegerField(null=True, blank=True)
    count1 = models.IntegerField(null=True, blank=True)
    item2id = models.IntegerField(null=True, blank=True)
    count2 = models.IntegerField(null=True, blank=True)
    item3id = models.IntegerField(null=True, blank=True)
    count3 = models.IntegerField(null=True, blank=True)
    modified = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=250, null=True, blank=True)

class Bills(models.Model):
    orderid = models.IntegerField(null=True, blank=True)
    totalcost = models.FloatField(null=True, blank=True)
    modified = models.IntegerField(null=True, blank=True)
    type = models.CharField(max_length=250, null=True, blank=True)
