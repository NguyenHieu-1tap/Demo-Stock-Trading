import socket
import time
from tabulate import tabulate
import colorama
from colorama import Fore, Style

# import pytz
from datetime import datetime

host = 'localhost'
port = 8050
state = ''
lst_stock = []


def create_data(msg):
    msg = msg + '\0'
    return msg.encode('utf-8')


def send_data(sk, msg):
    # send
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
    return msg


def confirm_action(state):
    print(Fore.RED + "SERVER WILL TAKE 5% FROM THE TRANSACTION !!!" + Fore.RESET)
    confirm = input('Do you want to {} this (YES/NO) '.format(state))
    if confirm == 'YES':
        return 'YES'
    if confirm == 'NO':
        return 'NO'

    confirm_action(state)


def menu_choice(client_name):
    print(client_name)
    menu = input('Chon chuc nang (ALL/BOARD/SEARCH/SELL/BUY/MY_STOCK/EXIT): ')
    input_data(sk, menu, client_name)


def input_data(sk, state, client_name):
    if state == 'ALL':
        print(Fore.CYAN + 'ALL STOCKS AVAILABLE: ' + Fore.RESET)
        send_data(sk, 'ALL')
        data = recv_data(sk)
        buying_stock, selling_stock = data.split('$!$')

        buying_stock = buying_stock.split('$$')
        selling_stock = selling_stock.split('$$')

        print(Fore.GREEN + 'Buyers:' + Fore.RESET)
        for x in buying_stock:
            print(x)

        print(Fore.GREEN + 'Sellers:' + Fore.RESET)
        for y in selling_stock:
            print(y)

        buying_stock.clear()
        selling_stock.clear()
        return

    if state == 'SEARCH':
        print('SEARCH')
        trader_name = input('Nhap ten trader: ')
        id = input('Nhap id: ')
        name = input('Nhap ten: ')
        money = str(input('Nhap tien: '))
        number = str(input('Nhap so luong: '))

        msg = state + '@@' + trader_name + '@@' + id + '@@' + name + '@@' + money + '@@' + number
        send_data(sk, msg)
        print(Fore.CYAN + 'FOUND THESE STOCKS: ' + Fore.RESET)
        data = recv_data(sk)
        lst_stock = data.split('@@')
        for i in lst_stock:
            print(i)
        lst_stock.clear()
        return

    if state == 'BOARD':
        print(Fore.CYAN + 'DASH BOARD' + Fore.RESET)
        send_data(sk, 'BOARD')
        data = recv_data(sk)
        top_legit, top_spent = data.split('$!$')

        top_legit = top_legit.split('$$')
        top_spent = top_spent.split('$$')

        print(Fore.GREEN + 'Top transaction trader' + Fore.RESET)
        for a in reversed(top_legit):
            print(a)

        print(Fore.GREEN + 'Top spent trader' + Fore.RESET)
        for b in reversed(top_spent):
            print(b)

        top_legit.clear()
        top_spent.clear()
        return


    if state == 'SELL':
        utc_time = datetime.utcnow()
        curr_time = time.localtime()
        local_time = time.strftime("%H:%M:%S", curr_time)

        print("SELL")
        trader_name = input('Nhap ten trader: ')
        id = input('Nhap id: ')
        name = input('Nhap ten: ')
        money = str(input('Nhap tien: '))
        number = str(input('Nhap so luong: '))

        if id == '' or name == '' or money == '' or number == '' or money.isnumeric() == False or number.isnumeric() == False:
            print(Fore.RED + 'Do you miss any fields ?' + Fore.RESET)
            return

        data = str(dict(trader_name=client_name, id=id, name=name, money=money, number=number))
        msg = state + '?' + client_name + '?' + id + '?' + name + '?' + money + '?' + number
        send_data(sk, msg)
        msg = recv_data(sk)
        if msg == 'Available':
            print(client_name + ' ' + id + ' ' + name + ' ' + money + ' ' + number)
            print(msg)
            yesno = confirm_action(state)
            order_request = client_name + '#SELL#' + state + '#SELL#' + trader_name + '#SELL#' + id + '#SELL#' + name + '#SELL#' + money + '#SELL#' + \
                            number + '#SELL#' + str(utc_time) + '#SELL#' + yesno

            send_data(sk, order_request)
            msg = recv_data(sk)
            msg = recv_data(sk)
            if msg == 'SUCCESSFUL':
                print(Fore.GREEN + client_name + ' ' + state + ' ' + data + ' ' + 'SUCCESSFUL !!!' + Fore.RESET)

                print('Local time: ', local_time)
                print('UTC time: ', utc_time)
                return

    if state == 'BUY':
        utc_time = datetime.utcnow()
        curr_time = time.localtime()
        local_time = time.strftime("%H:%M:%S", curr_time)

        print('BUY')
        trader_name = input('Nhap ten trader: ')
        id = input('Nhap id: ')
        name = input('Nhap ten: ')
        money = str(input('Nhap tien: '))
        number = str(input('Nhap so luong: '))

        if id == '' or name == '' or money == '' or number == '' or money.isnumeric() == False or number.isnumeric() == False:
            print(Fore.RED + 'Do you miss any fields ?' + Fore.RESET)
            return

        data = str(dict(trader_name=trader_name, id=id, name=name, money=money, number=number))
        msg = state + '?' + trader_name + '?' + id + '?' + name + '?' + money + '?' + number
        send_data(sk, msg)
        msg = recv_data(sk)
        if msg == 'Available':
            print(trader_name + ' ' + id + ' ' + name + ' ' + money + ' ' + number)
            print(msg)
            yesno = confirm_action(state)
            order_request = client_name + '#BUY#' + state + '#BUY#' + trader_name + '#BUY#' + id + '#BUY#' + name + '#BUY#' + money + '#BUY#' + \
                            number + '#BUY#' + str(utc_time) + '#BUY#' + yesno
            send_data(sk, order_request)
            msg = recv_data(sk)
            msg = recv_data(sk)
            if msg == 'SUCCESSFUL':
                print(Fore.GREEN + client_name + ' ' + state + ' ' + data + ' ' + 'SUCCESSFUL !!!' + Fore.RESET)

                print('Local time: ', local_time)
                print('UTC time: ', utc_time)
                return

    if state == 'MY_STOCK':
        client_name = client_name + '!!'
        send_data(sk, client_name)
        msg = recv_data(sk)
        name, point, spent, curr_money, buy_order, sell_order = msg.split('!!')

        a = [[Fore.CYAN + 'Username:', Fore.GREEN + name, Fore.CYAN + 'Current money:', Fore.GREEN +  curr_money],
             [Fore.CYAN + 'Legit point:', Fore.RED + point, Fore.CYAN + 'Life time spent:', Fore.RED + spent + Fore.RESET]]
        print(tabulate(a))
        print('Buy order: ')
        buy_order = buy_order.split('...')
        for x in buy_order:
            print(x)

        print('Sell order: ')
        sell_order = sell_order.split('...')
        for y in sell_order:
            print(y)

    if state == 'EXIT':
        return


def login(sk):
    client_name = input('Username Password (EXIT to exit): ')
    if client_name == 'EXIT':
        return 'EXIT'

    if ' ' not in client_name:
        print('Your Username or Password is missing !!!')
        return 'EXIT'

    return client_name


if __name__ == '__main__':
    while True:
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.connect((host, port))
            client_name = input('Username Password (EXIT to exit): ')

            if client_name == 'EXIT':
                break

            if ' ' in client_name:
                user_name, password = client_name.split()
                client_name = user_name + '***' + password
                send_data(sk, client_name)
                msg = recv_data(sk)
                if msg == 'Approved':
                    menu_choice(user_name)
                if msg == 'Denied':
                    print('Your Username or Password is not correct !!!')

        except ConnectionError:
            print('Error')
            break
        finally:
            sk.close()
