from myprofile.models import Inventory, Orders, Bills
from celery import shared_task

@shared_task
def notification(orderid, type):
    with open("data/notifications.out", "a") as file:
        file.write(f"{type} | OrderID: {orderid}\n")

@shared_task
def fulfill(billid):
    bll = Bills.objects.get(id=billid)
    ord = Orders.objects.get(id=bll.orderid)
    if ord.modified == bll.modified and ord.status == "in process":
        ord.status = "shipped"
        ord.save()
        notification.delay(ord.id, "shipped")

@shared_task
def bill(orderid, type):
    ord = Orders.objects.get(id=orderid)
    inv1 = Inventory.objects.get(id=ord.item1id)
    inv2 = Inventory.objects.get(id=ord.item2id)
    inv3 = Inventory.objects.get(id=ord.item3id)
    totalcost = inv1.unitcost * ord.count1 + inv2.unitcost * ord.count2 + inv3.unitcost * ord.count3
    modified = ord.modified
    bll = Bills()
    bll.orderid = orderid
    bll.totalcost = totalcost
    bll.modified = modified
    bll.type = type
    bll.save()
    if type == "retail":
        fulfill.delay(bll.id)
    elif type == "refund":
        notification.delay(orderid, "refunded")
    else:
        print("bill type invalid")
