import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable
import os
import datetime
from tqdm import tqdm
import threading, time
import getkey
tickets = {}  # Список ссылок тикетов акций
cache = []  # кэш значий акций предыдучей итерации
buy_pr = 45
sell_pr = 85

select = 1
table = None
print_st = False
print_st2 = True
# Color
R = "\033[0;31;40m"  # RED
G = "\033[0;32;40m"  # GREEN
N = "\033[0m"  # Reset
B = "\033[0;34;40m"  # Blue
Y = '\033[0;33m'  # Yellow

# Hat
hat = str(B+"G"+R+'o'+Y+'o'+B+'g'+G+'l'+R+'e'+Y+" Finanse"+N+"\n Input settings: " +
        "|"+B+"s"+N+"ell (price>"+str(sell_pr)+"%max)|" + " |"+G+"b"+N+"uy (price<min+"+str(buy_pr)+"%)|" + Y + " d"+N + " - set default \n" +
      ' Tickets config: '+'|'+Y+'A'+N+' - add new ticket|'+' |'+Y+'D'+N+' - delete ticket| |select table: 1, 2, 3|')
print(hat)   
# Считываем индексы из файла и формируем список ссылок
def getUrl():
    global tickets
    tickets = {}
    data = open('data.txt', 'r')  # Фаил индексов акий
    for i in data.read().split('\n'):
        if i != '':
            tickets[i] = "https://www.google.com/finance/quote/" + i + \
                ":MCX?sa=X&ved=2ahUKEwjK5-z-yJLyAhUhpIsKHXbMBh0Q_AUoAXoECAEQAw"
    data.close()
getUrl()
# Заголовок эмуляции браузера
headers = {
    'user agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.135 Safari/537.36"}


# Функция обновления тикетов и построения таблици
def update_ticker():
    global cache, table, print_st
    # Формируем таблицу
    th = ["Name", "Price", "¤", "%",
          "UpdateTime", 'RangePerYear', 'Action', "   ~  "]
    table = PrettyTable(th)
    td = []
    # Получаем данные по ссылкам
    getUrl()
    for i in tqdm(tickets, bar_format='{l_bar}{bar:80}'):
        # Получаем html код по ссылкам
        try:
            html = requests.get(tickets[i], headers)
            soup = BeautifulSoup(html.content, 'html.parser')  # парсер HTML

            # Ищем div блок с содержимым значения индекса акции
            convert = soup.findAll('div', {'class': 'YMlKec fxKbKc'})
            # Ищем div блок с содержимым значения годового ренжа
            Range_per_year = soup.findAll('div', {'class': 'P6K39c'})

            RangePerYear = Range_per_year[2].text  # Годовая разница
            currency = convert[0].text[0]  # тип валюты
            price = convert[0].text[1:]  # Значение индекса

            # Вставляем данные в массив данных для таблици
            td.append([i, price, currency, '   %   ', "--:--",
                    RangePerYear, "    *    ", "   ~  "])
        
        # Ошибка получения тикета удаляем его из файла data
        except:
            data = open('data.txt', 'r')
            old_data = data.read()
            data.close()
            old_data = old_data.split('\n')
            data = open('data.txt', 'w+')
            for _ in old_data:
                if _ != '' and _ != tickets[i].split('quote/')[1].split(':MCX?')[0]:
                    data.write(_+"\n")
            data.close()
            
    # Создаем таблицу
    table = PrettyTable(th)
    x = 0
    for i in td:
        if "," in i[1]:
            i[1] = i[1].split(",")[0] + "." + i[1].split(",")[1].split(".")[0]
        if cache != []:
            if float(i[1]) < float(cache[x][1].split("m")[0]):
                a = float(i[1])
                b = float(cache[x][1])
                i[3] = R+"↓ "+str(100*(a-b)/a)[0:5] + "%" + N
                i[4] = str(datetime.datetime.now().hour) + ':' + \
                    str(datetime.datetime.now().minute) + ':' + \
                    str(datetime.datetime.now().second)
                # минимальное значение цены
                v = i[5].split(' ')[0].split('₽')[1]
                if ',' in v:
                    v = v.split(',')[0] + '.' + v.split(',')[1].split('.')[0]
                if float(i[1]) < float(v) or float(i[1]) >= float(v) and float(i[1]) < float(v) + ((float(v)*buy_pr)/100):
                    i[6] = G+"!!!Buy!!!"
            else:
                a = float(i[1])
                b = float(cache[x][1])
                i[3] = G+'↑ '+str(100*(a-b)/a)[0:5] + "%" + N
                i[4] = str(datetime.datetime.now().hour) + ':' + \
                    str(datetime.datetime.now().minute) + \
                    ':' + str(datetime.datetime.now().second)
                # Максимальное значение цены
                v = i[5].split(' ')[2].split('₽')[1]
                if ',' in v:
                    v = v.split(',')[0] + '.' + v.split(',')[1].split('.')[0]
                if float(i[1]) >= (float(v)*sell_pr)/100:
                    i[6] = B+"!!!SELL!!!"+N
                    i[7] = '~ '+str((float(v)*sell_pr)/100)[0:6]+i[2]

            table.add_row(i)
        else:
            i[6] = '    *    '
            table.add_row(i)
        x += 1
    print_st = True
    cache = td
    time.sleep(2)
    update_ticker()


# User input thread
def UserInput():
    global sell_pr, buy_pr, select
    while True:
        key = getkey.getkey()
        match key:
            case "s":
                try:
                    sell_pr = int(input("Sell %:"))
                except:
                    print('input value 1...100')
            case 'b':
                try:
                    buy_pr = int(input('Buy %'))
                except:
                    print('input value 1...100')
            case 'd':
                print('Buy and Sell set to default')
                sell_pr = 85
                buy_pr = 45
            case 'A':
                data = open('data.txt', 'a')
                data.write("\n"+input('Input ticket:').upper())
                data.close()
            case "D":
                ticketToDel = input('Input del ticket:').upper()
                data = open('data.txt', 'r')
                old_data = data.read()
                data.close()
                old_data = old_data.split('\n')
                new_data = []
                if ticketToDel in old_data:
                    for i in old_data:
                        if i !='' and i != ticketToDel:
                            new_data.append(i)
                    data = open('data.txt', 'w+')
                    for i in new_data:
                        data.write(i+'\n')
                    data.close()
                    new_data = []
                    old_data = []
                else:
                    print('Nothing to del')
            case '1':
                select = 1
            case '2':
                select = 2

# Print table depending on select
def printing():
    global print_st, print_st2, table
    while True:
        time.sleep(1)
        match select:
            case 1:
                if print_st:
                    os.system("clear")
                    print(hat)
                    print(table)
                    print_st = False
            case 2:
                if print_st2:
                    os.system("clear")
                    print(hat)
                    print_st2 = False
#Threads
thread_userinput = threading.Thread(target=UserInput, args=())
thread_userinput.start()
# update ticket in thread
threadUpdateTicket = threading.Thread(target=update_ticker, args=())
threadUpdateTicket.start()
# Printing thread
printingThread = threading.Thread(target=printing, args=())
printingThread.start()
