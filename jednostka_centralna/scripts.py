import pygame
import time
import re

def get_config_value(var_name):
    """
    Otwiera plik 'config/variables', szuka linii, która zaczyna się od var_name + "=",
    a następnie zwraca wartość znajdującą się po znaku "=".
    Jeśli zmienna nie zostanie znaleziona, funkcja zwraca None.
    """
    try:
        with open("config/variables", "r") as file:
            for line in file:
                # Usuwamy zbędne białe znaki na początku i końcu linii
                line = line.strip()
                # Sprawdzamy, czy linia zaczyna się od var_name=
                if line.startswith(var_name + "="):
                    # Dzielenie tylko na dwie części: przed i po pierwszym '='
                    _, value = line.split("=", 1)
                    return value.strip()  # usuwamy ewentualne spacje
    except FileNotFoundError:
        print("Plik 'config/variables' nie został znaleziony.")
    return None

# Przykładowe użycie:
# value = get_config_value("moja_zmienna")
# print(value)

def print_timers(screen, timers, czas_oczekiwania_na_ruch_w_pokoju, czas_wygasania_czujnikow):
    x = 500
    y = 50
    font = pygame.font.SysFont(None, 48)
    font_color = (255, 0, 25)

    line = "[D] time.time(): " + str(int(time.time()))
    text_surface = font.render(line, True, font_color)
    screen.blit(text_surface, (x, y))
    y += 48

    if(timers[2] != 0):
        line = None
        if int(time.time() - timers[2] + czas_oczekiwania_na_ruch_w_pokoju) > 0:
            line = "[D] timer[ppok]-time+czas: " + str(timers[2] + czas_oczekiwania_na_ruch_w_pokoju - int(time.time()))
        else:
            line = "[D] time-timer[ppok]+czas: 0"
        text_surface = font.render(line, True, font_color)
        screen.blit(text_surface, (x, y))
        y += 48

    if (timers[1] != 0):
        line = None
        if int(time.time() - timers[1] + czas_oczekiwania_na_ruch_w_pokoju) > 0:
            line = "[D] timer[salo]-time+czas: " + str(timers[1] + czas_oczekiwania_na_ruch_w_pokoju - int(time.time()))
        else:
            line = "[D] time-timer[salo]+czas: 0"
        text_surface = font.render(line, True, font_color)
        screen.blit(text_surface, (x, y))
        y += 48

def update_variables(czas_wygasania_text, czas_oczekiwania_text):
    path = "config/variables"

    if not czas_wygasania_text.isdigit() or not czas_oczekiwania_text.isdigit():
        print("Błąd: wartość nie jest liczbą całkowitą.")
        return False

    try:
        with open(path, "r") as file:
            lines = file.readlines()

        updated_wygasania = False
        updated_oczekiwania = False

        with open(path, "w") as file:
            for line in lines:
                if line.startswith("czas_wygasania_czujnikow="):
                    file.write(f"czas_wygasania_czujnikow={czas_wygasania_text}\n")
                    updated_wygasania = True
                elif line.startswith("czas_oczekiwania_na_ruch_w_pokoju="):
                    file.write(f"czas_oczekiwania_na_ruch_w_pokoju={czas_oczekiwania_text}\n")
                    updated_oczekiwania = True
                else:
                    file.write(line)

        if updated_wygasania or updated_oczekiwania:
            print("Zmienna(e) została(y) zaktualizowana(e).")
        else:
            print("Nie znaleziono żadnej zmiennej do aktualizacji.")
        return updated_wygasania or updated_oczekiwania

    except FileNotFoundError:
        print("Plik konfiguracyjny nie istnieje.")
        return False

def print_debug(screen, ludzie):
    if get_config_value("debug") == "1":
        x = 50
        y = 50
        font = pygame.font.SysFont(None, 48)
        font_color = (255, 0, 25)

        line = "[D] Salon:          " + str(ludzie[1])
        text_surface = font.render(line, True, font_color)
        screen.blit(text_surface, (x, y))
        y += 48

        line = "[D] Przedpokoj: " + str(ludzie[2])
        text_surface = font.render(line, True, font_color)
        screen.blit(text_surface, (x, y))
