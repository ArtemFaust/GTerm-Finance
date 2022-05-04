import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable
import os
import datetime
from tqdm import tqdm
import threading
import time
import getkey
import sqlite3
import time

tz = time.tzname[0]
tickets = {}  # Список ссылок тикетов акций
cache = []  # кэш значий акций предыдучей итерации
buy_pr = 25
sell_pr = 85

select = 1  # Select print table
table = None
print_st = False
print_st2 = True
figs = {}
graph_period = '1m'
fig_to_show = None

# Color
R = "\033[0;31;40m"  # RED
G = "\033[0;32;40m"  # GREEN
N = "\033[0m"  # Reset
B = "\033[0;34;40m"  # Blue
Y = '\033[0;33m'  # Yellow

# Hat
hat = str(B+"G"+R+'o'+Y+'o'+B+'g'+G+'l'+R+'e'+Y+" Finanse"+N+"\n Input settings: " +
          "|"+B+"s"+N+"ell (price>"+str(sell_pr)+"%max)|" + " |"+G+"b"+N+"uy (price<min+"+str(buy_pr)+"%)|" + Y + " d"+N + " - set default \n" +
          ' Tickets config: '+'|'+Y+'A'+N+' - add new ticket|'+' |'+Y+'D'+N+' - delete ticket| |select view:' + Y+' 1, 2, 3'+N+'|'+Y+' G'+N+' - Graph period: %s ' % graph_period + '(1d, 3d, 1m)\n' +
            Y+' T'+N+' - set ticket to graph')
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

# функция Выполнение sql запроса для получения полей тикетов


def sql_execute(sql):
    sqlite_connection = sqlite3.connect('ticket.db')
    cursor = sqlite_connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    sqlite_connection.commit()
    cursor.close()
    sqlite_connection.close()
    sqlite_connection = None
    return rows


# Заголовок эмуляции браузера
headers = {
    'user agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.135 Safari/537.36"}


# Update global parameters
def refrasher():
    global hat
    hat = str(B+"G"+R+'o'+Y+'o'+B+'g'+G+'l'+R+'e'+Y+" Finanse"+N+"\n Input settings: " +
              "|"+B+"s"+N+"ell (price>"+str(sell_pr)+"%max)|" + " |"+G+"b"+N+"uy (price<min+"+str(buy_pr)+"%)|" + Y + " d"+N + " - set default \n" +
              ' Tickets config: '+'|'+Y+'A'+N+' - add new ticket|'+' |'+Y+'D'+N+' - delete ticket| |select view:' + Y+' 1, 2, 3'+N+'|'+Y+' G'+N+' - Graph period: %s ' % graph_period + '(1d, 3d, 1m)\n' +
              Y+' T'+N+' - set ticket to graph')


# Функция обновления тикетов и построения таблици
def update_ticker():
    global cache, table, print_st, print_st, figs
    print_st = False
    # Формируем таблицу
    th = ["Name", "Price", "¤", "%",
          "UpdateTime", 'RangePerYear', 'Action', "   ~  ", "DY", ' 📈 TL 📉 ']
    table = PrettyTable(th)
    td = []
    # Получаем данные по ссылкам
    getUrl()
    for i in tqdm(tickets, bar_format='{l_bar}{bar:100}'):
        # Получаем html код по ссылкам
        atempt = True  # Переключатель попыток
        for _ in range(3):  # 3 попытки получния данных
            if atempt:
                try:
                    html = requests.get(tickets[i], headers)
                    soup = BeautifulSoup(
                        html.content, 'html.parser')  # парсер HTML
                    # Ищем div блок с содержимым значения индекса акции
                    convert = soup.findAll('div', {'class': 'YMlKec fxKbKc'})
                    # Ищем div блок с содержимым значения годового ренжа
                    Range_per_year = soup.findAll('div', {'class': 'P6K39c'})

                    RangePerYear = Range_per_year[2].text  # Годовая разница
                    # Дивидендная доходность
                    dividend_yield = Range_per_year[5].text
                    currency = convert[0].text[0]  # тип валюты
                    price = convert[0].text[1:]  # Значение индекса
                    # Вставляем данные в массив данных для таблици
                    td.append([i, price, currency, '   %   ', "--:--",
                               RangePerYear, "    *    ", "   ~  ", dividend_yield, '📈🐄 or 🐻📉'])
                    atempt = False  # Если данные получины прекращаем попытки по данному тикету
                    # Встанвка данных в БД
                    if tz == '+3':
                        if datetime.datetime.now().hour < 19 and float(str(datetime.datetime.now().hour) + '.' + str(datetime.datetime.now().minute)) > 9.30:
                            try:
                                if "," in price:
                                    price = price.split(",")[0] + "." + \
                                        price.split(",")[1].split(".")[0]
                                # Вставка данных по тикету в БД
                                sqlite_connection = sqlite3.connect(
                                    'ticket.db')
                                cursor = sqlite_connection.cursor()
                                sql = """INSERT INTO ticket_data (TicketName, Year, Month, Day, Hour, Minute, Second, IndexValue) VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7});""".format(
                                    "'"+str(i)+"'", "'"+str(datetime.datetime.now().year)+"'", "'"+str(
                                                    datetime.datetime.now().month)+"'", "'"+str(datetime.datetime.now().day)+"'",
                                    "'"+str(datetime.datetime.now().hour)+"'", "'"+str(datetime.datetime.now().minute)+"'", "'"+str(datetime.datetime.now().second)+"'", float(price))
                                cursor.execute(sql)
                                sqlite_connection.commit()
                                cursor.close()
                                sqlite_connection.close()
                                sqlite_connection = None
                            except Exception as ex:
                                log = open('log.txt', 'a')
                                log.write(str(type(ex)) + '\n' +
                                          str(ex) + ' line 131' + '\n\n\n')
                                log.close()
                # Ошибка получения тикета удаляем его из файла data
                except Exception as ex:
                    log = open('log.txt', 'a')
                    log.write(str(type(ex)) + '\n' +
                              str(ex) + ' line 109' + '\n\n\n')
                    log.close()

    # Создаем таблицу
        table = PrettyTable(th)
        x = 0
        for i in td:
            if cache != [] and i[1] != '-' and cache[x][1].split("m")[0] != '-':
                try:
                    if "," in i[1]:
                        i[1] = i[1].split(",")[0] + "." + \
                            i[1].split(",")[1].split(".")[0]
                    if cache != [] and len(cache) == len(td):
                        if float(i[1]) <= float(cache[x][1].split("m")[0]):
                            a = float(i[1])
                            b = float(cache[x][1])
                            i[3] = R+"↓ "+str(100*(a-b)/a)[0:5] + "%" + N
                            i[4] = str(datetime.datetime.now().hour) + ':' + \
                                str(datetime.datetime.now().minute) + ':' + \
                                str(datetime.datetime.now().second)
                            # минимальное значение цены
                            v = i[5].split(' ')[0].split('₽')[1]
                            if ',' in v:
                                v = v.split(',')[0] + '.' + \
                                    v.split(',')[1].split('.')[0]
                            # Безусловный процент покупки
                            if float(i[1]) < float(v) or float(i[1]) >= float(v) and float(i[1]) < float(v) + ((float(v)*buy_pr)/100):
                                i[6] = G+"!!!Buy!!!"+N
                                i[7] = '~ ' + \
                                    str(float(v) +
                                        ((float(v)*buy_pr)/100))[0:6]
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
                                v = v.split(',')[0] + '.' + \
                                    v.split(',')[1].split('.')[0]
                            # Безусловный процент продажи
                            if float(i[1]) >= (float(v)*sell_pr)/100:
                                i[6] = B+"!!!SELL!!!"+N
                                i[7] = '~ ' + \
                                    str((float(v)*sell_pr)/100)[0:6]+i[2]

                        # Получаем данные из ДБ
                        if graph_period == '1d':  # переиод 1 день
                            sql = """select * from ticket_data where TicketName = '{0}' and Year = '{1}' and Month = '{2}' and Day = '{3}';""".format(
                                str(i[0]), str(datetime.datetime.now().year), str(datetime.datetime.now().month), str(datetime.datetime.now().day))
                        elif graph_period == '3d':
                            sql = """select * from ticket_data where TicketName = '{0}' and Year = '{1}' and Month = '{2}' and Day = '{3}' and Day = '{4}' and Day = '{5}';""".format(
                                str(i[0]), str(datetime.datetime.now().year), str(datetime.datetime.now().month), str(datetime.datetime.now().day-2), 
                                str(datetime.datetime.now().day-1), str(datetime.datetime.now().day))
                        elif graph_period == '1m':
                            sql = """select * from ticket_data where TicketName = '{0}' and Year = '{1}' and Month = '{2}';""".format(
                                str(i[0]), str(datetime.datetime.now().year), str(datetime.datetime.now().month))
                        rows = sql_execute(sql)
                        all_day_value_list = []
                        for _ in rows:
                            all_day_value_list.append(list(_)[7])

                        # Данные для графика
                        figs[i[0]] = [all_day_value_list]

                        table.add_row(i)
                    else:
                        i[6] = '    *    '
                        table.add_row(i)
                    x += 1
                except Exception as ex:
                    log = open('log.txt', 'a')
                    log.write(str(type(ex)) + '\n' +
                              str(ex) + ' line 204' + '\n\n\n')
                    log.close()
    print_st = True
    cache = td
    time.sleep(1.2)
    update_ticker()


# User input thread
def UserInput():
    global sell_pr, buy_pr, select, hat, fig_to_show, graph_period
    while True:
        key = getkey.getkey()
        match key:
            case "s":
                try:
                    sell_pr = int(input("Sell %:"))
                    refrasher()
                except Exception as ex:
                    print('input value 1...100')
                    log = open('log.txt', 'a')
                    log.write(str(type(ex)) + '\n' +
                              str(ex) + ' line 167' + '\n\n\n')
                    log.close()
            case 'b':
                try:
                    buy_pr = int(input('Buy %'))
                    refrasher()
                except Exception as ex:
                    print('input value 1...100')
                    log = open('log.txt', 'a')
                    log.write(str(type(ex)) + '\n' +
                              str(ex) + ' line 176' + '\n\n\n')
                    log.close()
            case 'd':
                print('Buy and Sell set to default')
                sell_pr = 85
                buy_pr = 45
                refrasher()
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
                        if i != '' and i != ticketToDel:
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
            case '3':
                select = 3
            case 'T':
                fig_to_show = input('Ticket?:').upper()
            case 'G':
                graph_period = input('Period?:')
                refrasher()


# Selecter: Print table depending on select
def printing():
    global print_st, print_st2, table, hat, figs, fig_to_show
    while True:
        time.sleep(0.5)
        match select:
            case 1:  # Print ticket table
                if print_st:
                    os.system("clear")
                    print(hat)
                    print(table)
                    print_st = False
            
            case 2:  # Print divident calendar table
                if print_st2:
                    os.system("clear")
                    print(hat)
                    #html = requests.get('https://open-broker.ru/analytics/dividend-calendar/', headers)
                    # soup = BeautifulSoup(html.content, 'html.parser')  # парсер HTML
                    # Ищем table блок с содержимым
                    # convert = soup.findAll('table', {
                    #                       'class': 'DividendCalendarTable_table__qX1ZS Table_table__fI87O Table_table--l__1LdnF'})
                    # print(convert)

            case 3:  # Print fig
                if print_st:
                    os.system("clear")
                    print(hat)
                    try:
                        if fig_to_show == None:
                            fig_to_show = list(figs.keys())[0]
                        fig = figs[fig_to_show]
                        print('Ticket: ' + Y+fig_to_show+N+' lenght: ' +
                              str(len(fig[0])) + ' price: ' + str(fig[0][-1]))
                        import plotext as plt
                        all = fig[0]
                        # all.reverse()

                        plt.plot_size(width=os.get_terminal_size().columns, height=os.get_terminal_size(
                        ).lines - 6)
                        plt.plot(all)
                        plt.theme('clear')
                        plt.show()
                        plt.cld()
                        plt.clc()
                        plt.clf()
                    except Exception as ex:
                        log = open('log.txt', 'a')
                        log.write(str(type(ex)) + '\n' +
                                  str(ex) + ' line 315' + '\n\n\n')
                        log.close()
                    print_st = False


# Threads
# User input thread
thread_userinput = threading.Thread(target=UserInput, args=())
thread_userinput.start()
# update ticket in thread
threadUpdateTicket = threading.Thread(target=update_ticker, args=())
threadUpdateTicket.start()
# Printing thread
printingThread = threading.Thread(target=printing, args=())
printingThread.start()
