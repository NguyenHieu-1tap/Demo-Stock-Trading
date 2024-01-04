import threading
import socket
import pymongo

host = 'localhost'
port = 8050
lst_user = []
lst_Stock = []

# Use mongoDB
DB_client = pymongo.MongoClient('mongodb://localhost:27017')
database = DB_client['Trading_Bot']
stock = database['Stock_4_Trade']
sell_orders = database['Sell_Order']
buy_orders = database['Buy_Order']
account = database['User']
success_trade = database['Successful_Trade']

for x in stock.find({}, {"_id": 0}):
    lst_Stock.append(x)

for user in account.find({}, {"_id": 0}):
    lst_user.append(user)


def create_socket(host, port):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.bind((host, port))
    sk.listen(5)
    return sk


def create_data(msg):
    msg = msg + '\0'
    return msg.encode('utf-8')


def send_message(sk, msg):
    data = create_data(msg)
    sk.sendall(data)


def recv_data(sk):
    data = bytearray()
    msg = ''
    while not msg:
        data1 = sk.recv(1024)
        if not data1:
            raise ConnectionError()
        data = data + data1
        if b'\0' in data1:
            msg = data.rstrip(b'\0')
    msg = msg.decode('utf-8')

    if '***' in msg:
        count = 0
        user_name, password = msg.split('***')
        for x in lst_user:
            if x['name'] == user_name and x['password'] == password:
                count += 1
        if count > 0:
            return 'Approved'
        return 'Denied'

    if msg == 'ALL':
        buying_stock = ''
        selling_stock = ''

        for x in reversed(lst_Stock):
            if x['status'] == 'WTB':
                buying_stock = str(x) + '$$' + buying_stock

            if x['status'] == 'WTS':
                selling_stock = str(x) + '$$' + selling_stock

        all_stock = buying_stock + '$!$' + selling_stock
        return all_stock

    if msg == 'BOARD':
        top_legit = ''
        top_spent = ''

        for a in account.find().sort('legit_point', -1).limit(3):
            top_legit = top_legit + '$$' + str([a['name'], a['legit_point']])

        for b in account.find().sort('money_spent', -1).limit(3):
            top_spent = top_spent + '$$' + str([b['name'], b['money_spent']])

        dash_board = top_legit + '$!$' + top_spent
        return dash_board

    if '@@' in msg:
        lst_search = ''
        state, trader_name, id, name, money, number = msg.split('@@')

        for x in reversed(lst_Stock):
            if x['user'] == trader_name or x['id'] == id or x['name'] == name or x['money'] == money or x['number'] == number:
                lst_search = str(x) + '@@' + lst_search

        send_message(sk, lst_search)
        lst_search = ''
        return lst_search


    if '?' in msg:
        state, trader, id, name, money, number = msg.split('?')

        if state == 'SELL':
            for x in lst_Stock:
                if x['user'] == trader and x['status'] == 'WTB' and x['id'] == id and x['name'] == name and x['money'] == money:
                    break
            return 'Available'

        if state == 'BUY':
            for x in lst_Stock:
                if x['user'] == trader and x['status'] == 'WTS' and x['id'] == id and x['name'] == name and x['money'] == money and int(x['number']) >= int(number):
                    break
            return 'Available'

    if '#SELL#' in msg:
        user, state, trader, id, name, money, number, time, confirm = msg.split('#SELL#')
        count = 0
        c = 0

        if state == 'SELL' and confirm == 'YES' and trader == '':
            for x in stock.find():
                if x['user'] == user and x['status'] == 'WTS' and x['id'] == id and x['name'] == name:
                    count += 1
                    break
            if count == 0:
                order = dict(user=user, status='WTS', id=id, name=name, money=money, number=number)

                stock.insert_one(order)

                print('ORDER UPLOADED')
                return 'SUCCESSFUL'

            myquery = {'user': user, 'status': 'WTS', "id": id, 'name': name}
            newvalues = {"$set": {"money": money, "number": number}}

            stock.update_one(myquery, newvalues)
            print(user, 'WTS', id, name, money, number)
            print('ORDER UPDATED')
            return 'SUCCESSFUL'

        if state == 'SELL' and confirm == 'YES' and trader != '':
            for x in stock.find():
                if x['user'] != user and x['status'] == 'WTB' and x['id'] == id and x['name'] == name:
                    number_remain = str(int(x['number']) - int(number))
                    total_money = str(int(money) * int(number))

                    print(user, 'WTS', id, name, money, number)
                    print('ORDER CONFIRMED')
                    count += 1
                    break

            if count == 0:
                order = dict(user=user, status='WTS', id=id, name=name, money=money, number=number)

                stock.insert_one(order)
                print('ORDER UPLOADED')
                return 'SUCCESSFUL'

            myquery = {'user': trader, 'status': 'WTB', "id": id, 'name': name, 'money': money}
            newvalues = {"$set": {"number": number_remain}}
            sell_order = dict(user=user, id=id, name=name, money=money, number=number, total=total_money, trader=trader,
                              time=time)

            stock.update_one(myquery, newvalues)
            sell_orders.insert_one(sell_order)

            profit = int(total_money)*5/100
            for a in account.find():
                if a['name'] == user :
                    point = a['legit_point'] + int(number)
                    cur_money = int(a['current_money']) + int(total_money) - profit
                    break

            myquery = {'name': user}
            newvalues = {"$set": {"legit_point": point, "current_money": cur_money}}
            account.update_one(myquery, newvalues)

            transaction = dict(user=user, state=state, id=id, name=name, money=money, number=number, total=total_money,
                               profit=profit)
            success_trade.insert_one(transaction)

            total_money = ''
            number_remain = ''
            return 'SUCCESSFUL'

    if '#BUY#' in msg:
        user, state, trader, id, name, money, number, time, confirm = msg.split('#BUY#')
        count = 0

        if state == 'BUY' and confirm == 'YES' and trader == '':
            for x in stock.find():
                if x['user'] == user and x['status'] == 'WTB' and x['id'] == id and x['name'] == name:
                    count += 1
                    break

            if count == 0:
                order = dict(user=user, status='WTB', id=id, name=name, money=money, number=number)

                stock.insert_one(order)
                print('ORDER UPLOADED')
                return 'SUCCESSFUL'

            myquery = {'user': user, 'status': 'WTB', "id": id, 'name': name}
            newvalues = {"$set": {"money": money, "number": number}}

            stock.update_one(myquery, newvalues)
            print(user, 'WTB', id, name, money, number)
            print('ORDER UPDATED')
            return 'SUCCESSFUL'

        if state == 'BUY' and confirm == 'YES' and trader != '':
            for x in stock.find():
                if x['user'] != user and x['status'] == 'WTS' and x['id'] == id and x['name'] == name and x['money'] == money and int(x['number']) >= int(number):
                    number_remain = str(int(x['number']) - int(number))
                    total_money = str(int(x['money']) * int(number))

                    print(user, 'WTB', id, name, money, number)
                    print('ORDER CONFIRMED')
                    count += 1
                    break

            if count == 0:
                order = dict(user=user, status='WTB', id=id, name=name, money=money, number=number)

                stock.insert_one(order)
                print('ORDER UPLOADED')
                return 'SUCCESSFUL'

            myquery = {'user': trader, 'status': 'WTS', "id": id, 'name': name, 'money': money}
            newvalues = {"$set": {"number": number_remain}}
            buy_order = dict(user=user, id=id, name=name, money=money, number=number,total=total_money, trader=trader,
                             time=time)

            stock.update_one(myquery, newvalues)
            buy_orders.insert_one(buy_order)

            profit = int(total_money) * 5 / 100
            for a in account.find():
                if a['name'] == user :
                    point = a['legit_point'] + int(number)
                    cur_money = int(a['current_money']) - int(total_money) - profit
                    break

            myquery = {'name': user}
            newvalues = {"$set": {"legit_point": point, "current_money": cur_money}}
            account.update_one(myquery, newvalues)

            transaction = dict(user=user, state=state, id=id, name=name, money=money, number=number, total=total_money,
                               profit=profit)
            success_trade.insert_one(transaction)

            total_money = ''
            number_remain = ''
            return 'SUCCESSFUL'

    if '!!' in msg:
        buy_order = ''
        sell_order = ''
        point = ''
        spent = ''
        curr_money = ''
        client_name = msg.strip('!!')

        for a in account.find({}, {"_id": 0}):
            if a['name'] == client_name:
                point = a['legit_point']
                spent = a['money_spent']
                curr_money = a['current_money']
        for x in sell_orders.find({}, {"_id": 0}):
            if x['user'] == client_name:
                sell_order = str(x) + '...' + sell_order
        for y in buy_orders.find({}, {"_id": 0}):
            if y['user'] == client_name:
                buy_order = str(y) + '...' + buy_order

        client_stock = client_name + '!!' + str(point) + '!!' + str(spent) + '!!' + str(curr_money) + '!!' + buy_order + '!!' + sell_order

        return client_stock

    return msg


def process_client(sk, addr):
    try:
        while True:
            msg = recv_data(sk)
            send_message(sk, msg)
            print(msg, 'main 1')
            msg = recv_data(sk)
            send_message(sk, msg)

            print('{}: {}'.format(addr, msg))
            send_message(sk, msg)
            print(msg, 'main 2')

            msg = recv_data(sk)
            print(msg, 'main 3')
            send_message(sk, msg)

    except ConnectionError:
        print('error')
    finally:
        sk.close()


if __name__ == '__main__':
    sk1 = create_socket(host, port)
    addr = sk1.getsockname()
    print('Local address {}'.format(addr))
    while True:
        client_sk, client_addr = sk1.accept()
        print('Client address: {}'.format(client_addr))
        thread = threading.Thread(target=process_client, args=[client_sk, client_addr], daemon=True)
        thread.start()
        print('Connect from: {}'.format(client_addr))
