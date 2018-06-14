# See readme.md for instructions on running this code.

from typing import Any, Dict
import requests
from bs4 import BeautifulSoup
import re
from isoweek import Week
from urllib.request import Request, urlopen
from datetime import datetime
from PyPDF2 import PdfFileWriter, PdfFileReader
from io import BytesIO
import os.path
import subprocess
import pdftotext

BASE_URL = "https://sites.google.com/site/fedorestbe/menu-fr/menu-noga-fr/noga_fr_{}_{}.pdf"
BASE_PDF_PATH = "{}-{}.pdf"
BASE_TXT_PATH = "{}-{}.txt"
BASE_DAILY_TXT_PATH = "{}-{}-{}.txt"
HEADERS_REGEX = [r'^Potage$', r'^Plat du jour', r'^Plat Végétarien', r'^Grill']
GOOGLE_SITE_BASE = 'https://sites.google.com'

class FedorestdHandler(object):
    def get_date():
        """ Return the current day of week (0-6), the current week (0-51) and the current year"""
        today = datetime.today()
        day = today.weekday()
        #day = 2 # TODO : remove, test purpose only
        week = today.isocalendar()[1]
        year = today.year
        return (day, week, year)

    @staticmethod
    def download_pdf():
        """ Download the current menu as PDF """
        (_, week, year) = FedorestdHandler.get_date()
        url = BASE_URL.format(week, year)
        path = BASE_PDF_PATH.format(year, week)

        remote = urlopen(Request(url)).read()
        file = BytesIO(remote)
        pdf = PdfFileReader(file)
        writer = PdfFileWriter()
        writer.addPage(pdf.getPage(0))
        with open(path, "wb") as out:
            writer.write(out)


    @staticmethod
    def get_pdf_path():
        """ Return the path to the current menu as PDF, download the PDF if necessary """
        (_, week, year) = FedorestdHandler.get_date()
        path = BASE_PDF_PATH.format(year, week)

        if not os.path.exists(path):
            FedorestdHandler.download_pdf()

        return path
    
    @staticmethod
    def create_txt():
        """ Create the current menu as TXT """
        (_, week, year) = FedorestdHandler.get_date()
        pdf_path = FedorestdHandler.get_pdf_path()
        txt_path = BASE_TXT_PATH.format(year, week)

        # subprocess.call(['pdftotext', pdf_path, txt_path])
        with open(pdf_path, "rb") as file_pdf:
            pdf = pdftotext.PDF(file_pdf)
            #print ("PDF : {} ".format(pdf[0]))
            with open(txt_path, 'w', encoding = 'utf-8') as file_txt:
                file_txt.write(pdf[0])
                file_txt.close()
            file_pdf.close()
        print ("File created ")
            

    @staticmethod
    def get_txt_path():
        """ Return the path of the current menu as TXT, create the TXT if necessary """
        (_, week, year) = FedorestdHandler.get_date()
        path = BASE_TXT_PATH.format(year, week)

        #if not os.path.exists(path):
        FedorestdHandler.create_txt()
        
        return path

    @staticmethod
    def get_week_menu():
        """ Return the content of this week menu """
        with open(FedorestdHandler.get_txt_path(), 'r', encoding='utf-8') as menu:
            lines = menu.readlines()[4:]
            for line in lines:
                yield line


    def parse_text_day(line, day):
        col_size = 36 
        start = col_size * day 
        end = col_size * day + col_size 
        strlen = len(line) 

        if start > strlen:
            return '' 
        
        if end >= strlen:
            end = strlen - 1

        if strlen - end < 4:
            end = strlen - 1 

        if end - start < 1:
            return ''


        return line[start:end].strip()

    @staticmethod
    def parse_week_menu():
        """ Parse the weekly menu and split it into 5 files, one for each day """

        (day, week, year) = FedorestdHandler.get_date()

        #if os.path.exists(today_menu_path):
        #    return

        menus = ["", "", "", "", ""]
        closed = [False, False, False, False, False]
        skip_meal = [False, False, False, False, False]
        i = 0
        chunk_size = 30

        for line in FedorestdHandler.get_week_menu():
            j = 0
            if line == '':
                continue 

            #print ("Line : {}".format(line.encode('utf-8')))

            while j <= 4:
                line_day = FedorestdHandler.parse_text_day(line,j) 
                j = j + 1
                if line_day == '':
                    continue
                menus[j-1] += line_day + "\n"
            
                
        for i, day_menu in enumerate(menus):
            with open(BASE_DAILY_TXT_PATH.format(year, week, i), 'w', encoding='utf-8') as out:
                out.write(day_menu)

    @staticmethod
    def get_today_menu():
        """ Get the menu for today """
        (day, week, year) = FedorestdHandler.get_date()

        if day < 0 or day > 4:
            return "C'est le weekend aujourd'hui..."

        today_menu_path = BASE_DAILY_TXT_PATH.format(year, week, day)

        print(today_menu_path)

        #if not os.path.exists(today_menu_path):
        FedorestdHandler.parse_week_menu()

        with open(today_menu_path, 'r', encoding='utf-8') as menu:
            return menu.read()

    def usage(self) -> str:
        return '''
        This is the FedoRest unofficial bot.
        '''

    @staticmethod
    def get_help_message() -> str:
        return (
            'Usage : \n'
            '* @fedorest list : list all available menus \n'
            '* @fedorest help : show this help message '
        )

    def get_menus_list(self):
        r = requests.get("https://sites.google.com/site/fedorestbe/menu-fr/menu-noga-fr")

        soup = BeautifulSoup(r.content, "lxml")

        current_week = Week.thisweek().week
        current_year = Week.thisweek().year

        content = ""

        content += "Voici les menus disponibles concoctes par les chefs Fedorest. Nous sommes en semaine {}-{} : \n".format(current_year, current_week)

        link_cells = soup.find_all("td", {"class": "td-file"})
        regex = r"noga_fr_(\d+)_(\d+)\.pdf"

        for cell in link_cells:
            links = cell.find_all("a")
            for link in links:
                url = link.get("href")
                matches = re.findall(regex, url)
                if matches:
                    (week, year) = matches[0]
                    content += "* ["+year + "-"+week + "](" + GOOGLE_SITE_BASE + url + ")\n"

        return content


    def handle_message(self, message: Any, bot_handler: Any) -> None:

        content = message['content']
       
        if content.strip() == 'list':
            try:
                bot_handler.send_reply(message, self.get_menus_list())
                return
            except Exception as inst:
                bot_handler.send_reply(message, "Une erreur est survenue : " + inst.message)
                return

        if content.strip() == 'today':
            bot_handler.send_reply(message, FedorestdHandler.get_today_menu())
            return

        bot_handler.send_reply(message, FedorestdHandler.get_help_message())
        return



handler_class = FedorestdHandler
