from django.http import JsonResponse
from myprofile.models import Inventory, Orders, Bills
from django.db import transaction
from myprofile.tasks import bill, notification
from myproject.settings import KAFKA_PRODUCER, KAFKA_CONSUMER
import random
import names

class OrderStatusFixed(Exception):
    pass

def createdata(request):
    if request.method == "GET":
        filename = request.GET["filename"]
        datasize = request.GET["datasize"]
        with open(f"data/{filename}", "w") as file:
            orderid = 0
            for i in range(int(datasize)):
                cmd = random.randint(1, 3)
                if cmd == 1:
                    name = names.get_full_name()[0:250]
                    item1id = random.randint(1,15)
                    count1 =  random.randint(0,2)
                    item2id = random.randint(1,15)
                    count2 = random.randint(0,2)
                    item3id = random.randint(1,15)
                    count3 = random.randint(0,2) 
                    file.write(f"place, {name}, {item1id}, {count1}, {item2id}, {count2}, {item3id}, {count3}\n")
                    orderid += 1
                elif cmd == 2:
                    id = random.randint(0, orderid)
                    item1id = random.randint(1,15)
                    count1 =  random.randint(0,2)
                    item2id = random.randint(1,15)
                    count2 = random.randint(0,2)
                    item3id = random.randint(1,15)
                    count3 = random.randint(0,2)
                    file.write(f"modify, {id}, {item1id}, {count1}, {item2id}, {count2}, {item3id}, {count3}\n")
                elif cmd == 3:
                    id = random.randint(0, orderid)
                    file.write(f"cancel, {id}\n")
                else:
                    return JsonResponse({"error": "order type invalid"})
        return JsonResponse({"error": "none"})
    return JsonResponse({"error": "method not supported"})

def runsimulation(request):
    if request.method == "GET":
        filename = request.GET["filename"]
        broker = request.GET["broker"]
        with open(f"data/{filename}", "r") as file:
            for order in file:
                if order == "\n":
                    continue
                words = [word.strip() for word in order.split(',')]
                if words[0] == "place":
                    customername = words[1]
                    item1id = int(words[2])
                    count1 =  int(words[3])
                    item2id = int(words[4])
                    count2 = int(words[5])
                    item3id = int(words[6])
                    count3 = int(words[7])
                    if count1 + count2 + count3 == 0:
                        continue
                    try:
                        with transaction.atomic():
                            # Inventory Updated
                            inv1 = Inventory.objects.get(id=item1id)
                            inv1.itemcount -= count1
                            inv1.save()
                            # Inventory Updated
                            inv2 = Inventory.objects.get(id=item2id)
                            inv2.itemcount -= count2
                            inv2.save()
                            # Inventory Updated
                            inv3 = Inventory.objects.get(id=item3id)
                            inv3.itemcount -= count3
                            inv3.save()
                            # Order Placed
                            ord = Orders()
                            ord.customername = customername
                            ord.item1id = item1id
                            ord.count1 = count1
                            ord.item2id = item2id
                            ord.count2 = count2
                            ord.item3id = item3id
                            ord.count3 = count3
                            ord.modified = 0
                            ord.status = "in process"
                            ord.save()
                        if broker == "rabbitmq":
                            bill.delay(ord.id, "retail")
                            notification.delay(ord.id, "placed")
                        elif broker == "kafka":
                            key = bytes("bill", encoding='utf-8')
                            value = bytes(f"{ord.id},retail", encoding='utf-8')
                            KAFKA_PRODUCER.send('orders', key=key, value=value)
                            key = bytes("notification", encoding='utf-8')
                            value = bytes(f"{ord.id},placed", encoding='utf-8')
                            KAFKA_PRODUCER.send('orders', key=key, value=value)
                        else:
                            return JsonResponse({"error": "broker invalid"})
                    except:
                        print("order not placed")
                elif words[0] == "modify":
                    id = int(words[1])
                    item1id = int(words[2])
                    count1 =  int(words[3])
                    item2id = int(words[4])
                    count2 = int(words[5])
                    item3id = int(words[6])
                    count3 = int(words[7])
                    if count1 + count2 + count3 == 0:
                        continue
                    try:
                        with transaction.atomic():
                            ord = Orders.objects.get(id=id)
                            if ord.status != "in process":
                                raise OrderStatusFixed()
                            # Inventory Updated
                            inv1 = Inventory.objects.get(id=ord.item1id)
                            inv1.itemcount += ord.count1
                            inv1.save()
                            # Inventory Updated
                            inv2 = Inventory.objects.get(id=ord.item2id)
                            inv2.itemcount += ord.count2
                            inv2.save()
                            # Inventory Updated
                            inv3 = Inventory.objects.get(id=ord.item3id)
                            inv3.itemcount += ord.count3
                            inv3.save()
                            # Inventory Updated
                            inv1 = Inventory.objects.get(id=item1id)
                            inv1.itemcount -= count1
                            inv1.save()
                            # Inventory Updated
                            inv2 = Inventory.objects.get(id=item2id)
                            inv2.itemcount -= count2
                            inv2.save()
                            # Inventory Updated
                            inv3 = Inventory.objects.get(id=item3id)
                            inv3.itemcount -= count3
                            inv3.save()
                            # Order Modified
                            ord.item1id = item1id
                            ord.count1 = count1
                            ord.item2id = item2id
                            ord.count2 = count2
                            ord.item3id = item3id
                            ord.count3 = count3
                            ord.modified += 1
                            ord.save()
                        if broker == "rabbitmq":
                            bill.delay(ord.id, "retail")
                        elif broker == "kafka":
                            key = bytes("bill", encoding='utf-8')
                            value = bytes(f"{ord.id},retail", encoding='utf-8')
                            KAFKA_PRODUCER.send('orders', key=key, value=value)
                        else:
                            return JsonResponse({"error": "broker invalid"})
                    except:
                        print("order not modified")
                elif words[0] == "cancel":
                    id = int(words[1])
                    try:
                        with transaction.atomic():
                            ord = Orders.objects.get(id=id)
                            if ord.status != "in process":
                                raise OrderStatusFixed()
                            # Inventory Updated
                            inv1 = Inventory.objects.get(id=ord.item1id)
                            inv1.itemcount += ord.count1
                            inv1.save()
                            # Inventory Updated
                            inv2 = Inventory.objects.get(id=ord.item2id)
                            inv2.itemcount += ord.count2
                            inv2.save()
                            # Inventory Updated
                            inv3 = Inventory.objects.get(id=ord.item3id)
                            inv3.itemcount += ord.count3
                            inv3.save()
                            # Order Cancelled
                            ord.status = "cancelled"
                            ord.save()
                        if broker == "rabbitmq":
                            bill.delay(ord.id, "refund")
                        elif broker == "kafka":
                            key = bytes("bill", encoding='utf-8')
                            value = bytes(f"{ord.id},refund", encoding='utf-8')
                            KAFKA_PRODUCER.send('orders', key=key, value=value)
                        else:
                            return JsonResponse({"error": "broker invalid"})
                    except:
                        print("order not cancelled")
                else:
                    return JsonResponse({"error": "order type invalid"})
        return JsonResponse({"error": "none"})
    return JsonResponse({"error": "method not supported"})

def runkafkaserver(request):
    if request.method == "GET":
        while True:
            for msg in KAFKA_CONSUMER:
                if msg.key.decode("utf-8") == "bill":
                    args = [arg.strip() for arg in msg.value.decode("utf-8").split(',')]
                    orderid = args[0]
                    type = args[1]
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
                        key = bytes("fulfill", encoding='utf-8')
                        value = bytes(f"{bll.id}", encoding='utf-8')
                        KAFKA_PRODUCER.send('orders', key=key, value=value)
                    elif type == "refund":
                        key = bytes("notification", encoding='utf-8')
                        value = bytes(f"{orderid},refunded", encoding='utf-8')
                        KAFKA_PRODUCER.send('orders', key=key, value=value)
                    else:
                        print("bill type invalid")
                elif msg.key.decode("utf-8") == "fulfill":
                    args = [arg.strip() for arg in msg.value.decode("utf-8").split(',')]
                    billid = args[0]
                    bll = Bills.objects.get(id=billid)
                    ord = Orders.objects.get(id=bll.orderid)
                    if ord.modified == bll.modified and ord.status == "in process":
                        ord.status = "shipped"
                        ord.save()
                        key = bytes("notification", encoding='utf-8')
                        value = bytes(f"{ord.id},shipped", encoding='utf-8')
                        KAFKA_PRODUCER.send('orders', key=key, value=value)
                elif msg.key.decode("utf-8") == "notification":
                    args = [arg.strip() for arg in msg.value.decode("utf-8").split(',')]
                    orderid = args[0]
                    type = args[1]
                    with open("data/notifications.out", "a") as file:
                        file.write(f"{type} | OrderID: {orderid}\n")
    return JsonResponse({"error": "method not supported"})
