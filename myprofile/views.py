from django.http import JsonResponse
from myprofile.models import Inventory, Orders
from django.db import transaction
from myprofile.tasks import bill, notification
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
                        bill.delay(ord.id, "retail")
                        notification.delay(ord.id, "placed")
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
                        bill.delay(ord.id, "retail")
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
                        bill.delay(ord.id, "refund")
                    except:
                        print("order not cancelled")
                else:
                    return JsonResponse({"error": "order type invalid"})
        return JsonResponse({"error": "none"})
    return JsonResponse({"error": "method not supported"})
