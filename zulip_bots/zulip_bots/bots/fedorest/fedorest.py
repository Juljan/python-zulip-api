# See readme.md for instructions on running this code.

from typing import Any, Dict
import requests
from bs4 import BeautifulSoup
import re
from isoweek import Week


GOOGLE_SITE_BASE = 'https://sites.google.com'

class FedorestdHandler(object):
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

        content += "Voici les menus disponibles. Nous sommes en semaine {} - {} : \n".format(current_year, current_week)

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


    def handle_message(self, message, bot_handler, state_handler):

        content = message['content']
       
        if content.strip() == 'list':
            bot_handler.send_reply(message, self.get_menus_list())
            return


        bot_handler.send_reply(message, self.get_help_message())
        return



handler_class = FedorestdHandler
