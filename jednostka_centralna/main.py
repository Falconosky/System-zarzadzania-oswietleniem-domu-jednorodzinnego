import os
import time
import scripts

os.environ["SDL_IM_MODULE"] = "ibus"
os.environ["SQUEEKBOARD_AUTOSHOW"] = "1"
os.environ["SDL_HINT_IME_SHOW_UI"] = "1"

import pygame
import sys
import paho.mqtt.client as mqtt

# Klasa symulująca wiadomość MQTT
class DummyMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload

import menu
import sensor_events

def on_message(client, userdata, msg):
    if not tryb_goscia:
        global payload, futryna_przedpokoj_state, futryna_salon_state, ruch_salon_state, ruch_przedpokoj_state
        # Dekodujemy payload do stringa i aktualizujemy zmienną
        payload = msg.payload.decode('utf-8').strip().lower()
        print("Odebrano na topic", msg.topic, ":", payload)
        if msg.topic == "przedpokoj/futryna/":
            futryna_przedpokoj_state = payload
        elif msg.topic == "salon/futryna/":
            futryna_salon_state = payload
        elif msg.topic == "salon/ruch/":
            ruch_salon_state = payload
        elif msg.topic == "przedpokoj/ruch/":
            ruch_przedpokoj_state = payload
        else:
            payload = payload  # dla pozostałych tematów

# Dane do połączenia
broker = "localhost"

client = mqtt.Client(
    client_id="MQTTPublisher",
    clean_session=True,
    userdata=None,
    protocol=mqtt.MQTTv311,
    transport="tcp"
)
client.connect(broker)  # Łączymy się z brokerem
client.subscribe("przedpokoj/futryna/", qos=2)
client.subscribe("salon/futryna/", qos=2)
client.subscribe("salon/ruch/", qos=2)
client.subscribe("przedpokoj/ruch/", qos=2)

client.on_message = on_message
client.loop_start()  # Uruchamiamy pętlę klienta MQTT w tle


pygame.init()
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.mouse.set_visible(False)
pygame.display.set_caption("Smart oswietlenie")

# Utworzenie obiektu font (None = domyślna czcionka, 48 = rozmiar czcionki)
font = pygame.font.SysFont(None, 48)
payload = "czujnik"
text_color = (255, 255, 255)
text_pos = (0, 0)

# Wyłączenie wejścia tekstowego, które mogłoby wywołać klawiaturę ekranową
# pygame.key.stop_text_input()
pygame.key.set_text_input_rect(pygame.Rect(0, 0, 0, 0))

input_state = {
    'text': "",
    'active': False,
    'error': None,
    'logged_in': False
}

czas_oczekiwania_state = {
'text': "",
    'active': False,
    'error': None
}

czas_wygasania_state = {
    'text': "",
    'active': False,
    'error': None
}

# Definicje kolorów
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# Ustawienia przycisku
button_width = 200
button_height = 100
button_x = (screen_width - button_width) // 2
button_y = (screen_height - button_height) // 2

#   Salon - 0.Kuchnia - 1.Salon - 2.Przedpokoj - 3.Lazienka - 4.Sypialnia1 - 5.Sypialnia2
swiatla = [False, False, False, False, False, False]
ludzie = [0, 0, 0, 0, 0, 0]
timers = [0, 0, 0, 0, 0, 0]
pomocnicze_timers = [0, 0, 0, 0, 0, 0]
ostatni_ruch_w_pokoju = [0, 0, 0, 0, 0, 0]
# 0 - brak ruchu    1 - ruch w pokoju
ruch_w_pokoju = [0, 0, 0, 0, 0, 0]
pokoje = [None] * 6
menu_events = []
czas_oczekiwania_na_ruch_w_pokoju = int(scripts.get_config_value("czas_oczekiwania_na_ruch_w_pokoju")) # w sekundach
czas_wygasania_czujnikow = int(scripts.get_config_value("czas_wygasania_czujnikow")) # w sekundach

# Inicjacja zmiennych dla przewijania menu
scroll_offset = 0         # aktualny offset pionowy
scrolling = False         # czy użytkownik aktualnie przeciąga
last_y = 0                # ostatnia pozycja y przy rozpoczęciu przeciągania
menu_position = 0
temp_ludzie_salon = 0
temp_ludzie_przedpokoj = 0

import settings
settings.screen = screen
settings.menu_events = menu_events
settings.menu_position = menu_position

clock = pygame.time.Clock()
redraw_needed = True  # flaga odświeżania
click_start = None
click_threshold = 10  # próg w pikselach
tap_processed = False
glowne_menu = True
last_salon = False
last_przedpokoj = False
tryb_goscia = False
futryna_przedpokoj_state = "false"
futryna_salon_state = "false"
ruch_salon_state = "false"
ruch_przedpokoj_state = "false"

pygame.key.stop_text_input()

czas_wygasania_state['text'] = scripts.get_config_value("czas_wygasania_czujnikow")
czas_oczekiwania_state['text'] = scripts.get_config_value("czas_oczekiwania_na_ruch_w_pokoju")

def show_settings():
    global menu_events, glowne_menu, menu_position
    glowne_menu = False
    menu_position = 1
    menu_events.clear()
    settings.show_settings(screen, menu_events, input_state)

def show_house():
    global pokoje, scroll_offset
    if glowne_menu==False:
        return
    try:
        if menu_events is not None:
            menu_events.clear()

        image_scale = 2
        border_thickness = 4 * 2

        dom = pygame.image.load("img/plan_domu_czarne.png").convert_alpha()
        if(not swiatla[0]):
            kuchnia = pygame.image.load("img/kuchnia_b.png").convert_alpha()
        else:
            kuchnia = pygame.image.load("img/kuchnia_y.png").convert_alpha()
        if(not swiatla[1]):
            salon = pygame.image.load("img/salon_b.png").convert_alpha()
        else:
            salon = pygame.image.load("img/salon_y.png").convert_alpha()
        if(not swiatla[2]):
            przedpokoj = pygame.image.load("img/przedpokoj_b.png").convert_alpha()
        else:
            przedpokoj = pygame.image.load("img/przedpokoj_y.png").convert_alpha()
        if (not swiatla[3]):
            lazienka = pygame.image.load("img/lazienka_b.png").convert_alpha()
        else:
            lazienka = pygame.image.load("img/lazienka_y.png").convert_alpha()
        if (not swiatla[4]):
            sypialnia1 = pygame.image.load("img/sypialnia1_b.png").convert_alpha()
        else:
            sypialnia1 = pygame.image.load("img/sypialnia1_y.png").convert_alpha()
        if (not swiatla[5]):
            sypialnia2 = pygame.image.load("img/sypialnia2_b.png").convert_alpha()
        else:
            sypialnia2 = pygame.image.load("img/sypialnia2_y.png").convert_alpha()

        dom = pygame.transform.scale(dom, (int(dom.get_width() * image_scale),
                                                   int(dom.get_height() * image_scale)))
        kuchnia = pygame.transform.scale(kuchnia, (int(kuchnia.get_width() * image_scale),
                                                   int(kuchnia.get_height() * image_scale)))
        salon = pygame.transform.scale(salon, (int(salon.get_width() * image_scale),
                                                   int(salon.get_height() * image_scale)))
        przedpokoj = pygame.transform.scale(przedpokoj, (int(przedpokoj.get_width() * image_scale),
                                                         int(przedpokoj.get_height() * image_scale)))
        sypialnia1 = pygame.transform.scale(sypialnia1, (int(sypialnia1.get_width() * image_scale),
                                               int(sypialnia1.get_height() * image_scale)))
        sypialnia2 = pygame.transform.scale(sypialnia2, (int(sypialnia2.get_width() * image_scale),
                                               int(sypialnia2.get_height() * image_scale)))
        lazienka = pygame.transform.scale(lazienka, (int(lazienka.get_width() * image_scale),
                                               int(lazienka.get_height() * image_scale)))

        screen.fill((0, 0, 0))

        # Koordynaty początkowe obrazka (łatwo modyfikowalne)
        image_initial_x = ((screen_width // 2) - dom.get_width()) // 2
        image_initial_y = ((screen_width // 2) - dom.get_width()) // 2

        pokoje[0] = kuchnia.get_rect()
        pokoje[0].left = image_initial_x + salon.get_width() - border_thickness
        pokoje[0].top = image_initial_y
        screen.blit(kuchnia, pokoje[0])

        pokoje[1] = salon.get_rect()
        pokoje[1].left = image_initial_x
        pokoje[1].top = image_initial_y
        screen.blit(salon, pokoje[1])

        pokoje[2] = przedpokoj.get_rect()
        pokoje[2].right = pokoje[0].right
        pokoje[2].top = image_initial_y + kuchnia.get_height() - border_thickness
        screen.blit(przedpokoj, pokoje[2])

        pokoje[4] = sypialnia1.get_rect()
        pokoje[4].left = image_initial_x
        pokoje[4].top = image_initial_y + salon.get_height() - border_thickness
        screen.blit(sypialnia1, pokoje[4])

        pokoje[3] = lazienka.get_rect()
        pokoje[3].left = pokoje[4].right - border_thickness
        pokoje[3].top = pokoje[4].top
        screen.blit(lazienka, pokoje[3])

        pokoje[5] = sypialnia2.get_rect()
        pokoje[5].left = pokoje[3].right - border_thickness
        pokoje[5].top = pokoje[4].top
        screen.blit(sypialnia2, pokoje[5])

        pygame.draw.rect(screen, (41, 41, 41), (screen_width // 2, 0, screen_width // 2, screen_height))
        pygame.draw.rect(screen, (110, 110, 110), (screen_width // 2 - 2, 0, 10, screen_height))
        scripts.print_debug(screen, ludzie)
        if scripts.get_config_value("debug") == "1":
            scripts.print_timers(screen, timers, czas_oczekiwania_na_ruch_w_pokoju, czas_wygasania_czujnikow)
        scroll_offset = menu.show_menu(screen, scroll_offset, screen_width // 2 - 2 + 10, 0, menu_events, tryb_goscia)
        return scroll_offset

    except pygame.error as e:
        print("Błąd wczytywania obrazu:", e)
        pygame.quit()
        sys.exit()

show_house()

client.publish("przedpokoj/swiatlo/", "false", qos=2)  # Publikujemy wiadomość do tematu
client.publish("salon/swiatlo/", "false", qos=2)  # Publikujemy wiadomość do tematu

# Główna pętla aplikacji
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_start = event.pos
            tap_processed = False
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if glowne_menu == False:
                continue
            if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
                print("Przycisk został naciśnięty!")
                client.publish("futryny/salon/", "5", qos=2)  # Publikujemy wiadomość do tematu

            elif pokoje[0] and pokoje[0].collidepoint(mouse_x, mouse_y):
                if(swiatla[0]):
                    swiatla[0] = False
                else:
                    swiatla[0] = True
                print("Kuchnia click!")
                show_house()
            elif pokoje[1] and pokoje[1].collidepoint(mouse_x, mouse_y) and not pokoje[2].collidepoint(mouse_x, mouse_y):
                if(swiatla[1]):
                    swiatla[1] = False
                    ludzie[1] = 0
                    client.publish("salon/swiatlo/", "false", qos=2)  # Publikujemy wiadomość do tematu
                else:
                    swiatla[1] = True
                    ludzie[1] = 1
                    client.publish("salon/swiatlo/", "true", qos=2)  # Publikujemy wiadomość do tematu
                print("Salon click!")
                show_house()
            elif pokoje[2] and pokoje[2].collidepoint(mouse_x, mouse_y):
                if(swiatla[2]):
                    swiatla[2] = False
                    ludzie[2] = 0
                    client.publish("przedpokoj/swiatlo/", "false", qos=2)  # Publikujemy wiadomość do tematu
                else:
                    swiatla[2] = True
                    ludzie[2] = 1
                    client.publish("przedpokoj/swiatlo/", "true", qos=2)  # Publikujemy wiadomość do tematu
                print("Przedpokoj click!")
                show_house()
            elif pokoje[3] and pokoje[3].collidepoint(mouse_x, mouse_y):
                message = None
                if(swiatla[3]):
                    swiatla[3] = False
                    message = "off"
                else:
                    swiatla[3] = True
                    message = "on"

                text_str = message
                print("Lazienka click!")
                show_house()
            elif pokoje[4] and pokoje[4].collidepoint(mouse_x, mouse_y):
                if (swiatla[4]):
                    swiatla[4] = False
                else:
                    swiatla[4] = True
                print("Sypialania1 click!")
                show_house()
            elif pokoje[5] and pokoje[5].collidepoint(mouse_x, mouse_y):
                if (swiatla[5]):
                    swiatla[5] = False
                else:
                    swiatla[5] = True
                print("Sypialania2 click!")
                show_house()
            elif mouse_x >= screen_width // 2 - 2 + 10:
                # Rozpoczynamy przeciąganie – zapisujemy pozycję y
                scrolling = True
                last_y = event.pos[1]
        elif event.type == pygame.MOUSEBUTTONUP:
            scrolling = False
            input_state['active'] = False
            czas_oczekiwania_state['active'] = False
            czas_wygasania_state['active'] = False
            pygame.key.stop_text_input()
            # Jeśli gest przewijania był duży, to nie traktujemy go jako kliknięcie
            if click_start is not None:
                dx = event.pos[0] - click_start[0]
                dy = event.pos[1] - click_start[1]
                if abs(dx) < click_threshold and abs(dy) < click_threshold:
                    if not tap_processed:  # obsłużemy tylko raz
                        for ev in menu_events:
                            if ev["rect"].collidepoint(event.pos):
                                if ev["name"] == "exit":
                                    print("Kliknięto kafelek wyjście do pulpitu")
                                    pygame.quit()
                                elif ev["name"] == "futryna_przedpokoj":
                                    dummy_msg = DummyMessage("przedpokoj/futryna/", b"true")
                                    on_message(None, None, dummy_msg)
                                    futryna_przedpokoj_state = payload
                                    sensor_events.futryna("przedpokoj")
                                elif ev["name"] == "futryna_salon":
                                    dummy_msg = DummyMessage("salon/futryna/", b"true")
                                    on_message(None, None, dummy_msg)
                                    futryna_salon_state = payload
                                    print("Kliknięto kafelek przejscie przez futryne do salonu")
                                    sensor_events.futryna("salon")
                                elif ev["name"] == "ruch_przedpokoj":
                                    dummy_msg = DummyMessage("przedpokoj/ruch/", b"true")
                                    on_message(None, None, dummy_msg)
                                    ruch_przedpokoj_state = payload
                                    print("Kliknięto kafelek ruchu w przedpokoju")
                                    sensor_events.ruch("przedpokoj")
                                elif ev["name"] == "ruch_salon":
                                    dummy_msg = DummyMessage("salon/ruch/", b"true")
                                    on_message(None, None, dummy_msg)
                                    ruch_salon_state = payload
                                    print("Kliknięto kafelek ruchu w salon")
                                    sensor_events.ruch("salon")
                                elif ev["name"] == "settings":
                                    menu_events.clear()
                                    print("Kliknięto kafelek ustawień")
                                    glowne_menu = False
                                    menu_position = 1
                                    show_settings()
                                elif ev["name"] == "back":
                                    print("Kliknięto ikone powrotu")
                                    glowne_menu = True
                                    menu_position = 0
                                    menu_events = []
                                    input_state['active'] = False
                                    input_state['text'] = ""
                                    input_state['error'] = None
                                    show_house()
                                elif ev['name'] == 'password':
                                    # Aktywujemy wpisywanie i ekranową klawiaturę
                                    print("Nacisnieto pole password")
                                    input_state['active'] = True
                                    input_state['error'] = None
                                    pygame.key.start_text_input()
                                    show_settings()
                                elif ev['name'] == 'czas_oczekiwania':
                                    # Aktywujemy wpisywanie i ekranową klawiaturę
                                    print("Nacisnieto pole czas_oczekiwania")
                                    czas_oczekiwania_state['active'] = True
                                    czas_oczekiwania_state['error'] = None
                                    pygame.key.start_text_input()
                                elif ev['name'] == 'czas_wygasania':
                                    # Aktywujemy wpisywanie i ekranową klawiaturę
                                    print("Nacisnieto pole czas_wygasania")
                                    czas_wygasania_state['active'] = True
                                    czas_wygasania_state['error'] = None
                                    pygame.key.start_text_input()
                                elif ev['name'] == 'save':
                                    scripts.update_variables(czas_wygasania_state['text'], czas_oczekiwania_state['text'])
                                    glowne_menu = True
                                    menu_position = 0
                                    czas_wygasania_czujnikow = scripts.get_config_value("czas_wygasania_czujnikow")
                                    czas_oczekiwania_na_ruch_w_pokoju = scripts.get_config_value("czas_oczekiwania_na_ruch_w_pokoju")
                                elif ev['name'] == 'przedpokoj_plus':
                                    if temp_ludzie_przedpokoj + temp_ludzie_salon < 4:
                                        temp_ludzie_przedpokoj += 1
                                elif ev['name'] == 'przedpokoj_minus':
                                    if temp_ludzie_przedpokoj > 0:
                                        temp_ludzie_przedpokoj -= 1
                                elif ev['name'] == 'salon_plus':
                                    if temp_ludzie_przedpokoj + temp_ludzie_salon < 4:
                                        temp_ludzie_salon += 1
                                elif ev['name'] == 'salon_minus':
                                    if temp_ludzie_salon > 0:
                                        temp_ludzie_salon -= 1
                                elif ev['name'] == 'check':
                                    tryb_goscia = False
                                    menu_position = 0
                                    ludzie[1] = temp_ludzie_salon
                                    temp_ludzie_salon = 0
                                    ludzie[2] = temp_ludzie_przedpokoj
                                    temp_ludzie_przedpokoj = 0
                                elif ev['name'] == 'tryb_goscia':
                                    if tryb_goscia == False:
                                        print("Włączono tryb gościa")
                                        tryb_goscia = True
                                    else:
                                        print("Wyłączono tryb gościa")
                                        menu_position = 3
                                else:
                                    print(f"Kliknięto kafelek o nazwie {ev['name']}")
                        tap_processed = True
                # Reset click_start po zakończeniu
                click_start = None
        elif event.type == pygame.MOUSEMOTION:
            if scrolling and glowne_menu:
                # Obliczamy przesunięcie w pionie
                dy = event.pos[1] - last_y
                last_y = event.pos[1]
                scroll_offset += dy
                if scroll_offset > 0:
                    scroll_offset = 0
                # Opcjonalnie: ogranicz scroll_offset do pewnych granic
                # np. scroll_offset = max(min(scroll_offset, max_scroll), min_scroll)
                redraw_needed = True
        elif event.type == pygame.TEXTINPUT or event.type == pygame.KEYDOWN:
            if(menu_position==1):
                hash_input = input_state['text']
                stored_hash = scripts.get_config_value("login_password_hash") or ""
                if hash_input == stored_hash:
                    menu_position=2
            settings.handle_login_event(event, input_state, czas_wygasania_state, czas_oczekiwania_state)

    # ------------------------------------------------------------------------------------------------------------------
    # LOGIKA ZAPALANIA SWIATEL
    # ------------------------------------------------------------------------------------------------------------------
    #   stany w pokojach:    0 - 0 ludzi
    #                        1 - 1 czlowiek itd...
    #                        100 - albo 1 albo 3 ludzi
    #                        101 - albo 2 albo 4 ludzi
    #   TIMERY
    # ------------------------------------------------------------------------------------------------------------------
    #   Timer z przedpokoju
    if timers[2] != 0:
        i = 2
        #   jeśli jedna osoba i nasluchujemy z tego pokoju to albo poszla albo nowa osoba
        if ludzie[i] == 1:
            # jeśli czas minął a ruchu brak to znaczy ze osoba ubyła
            if int(time.time()) - timers[i] > czas_oczekiwania_na_ruch_w_pokoju:
                ludzie[i] -= 1
                timers[i] = 0
            #   jeśli czas prośby (timer) jest starszy od ruchu w pokoju i nie minął czas oczekiwania
            #   to znaczy ze osoba przybyła do tego po
            #   TODO uwzglednic kiedyś że czujnik ruchu podaje informacje jeszcze po tym jak sie wyjdzie z obszaru
            elif (timers[i]<ostatni_ruch_w_pokoju[i] and
                int(time.time()) - timers[i] < czas_oczekiwania_na_ruch_w_pokoju):
                if(ludzie[1] == 0 or ludzie[1] == 1 or ludzie[1] == 2):
                    ludzie[i] += 1
                elif(ludzie[1] == 100):
                    ludzie[i] += 1
                    ludzie[1] = 1
                elif(ludzie[1] == 101):
                    ludzie[i] += 1
                    ludzie[1] = 2
                timers[i] = 0
        # ktos albo przsyszedl albo wyszedl dlatego albo 1 albo 3 ludzi
        elif ludzie[i] == 2:
            if(ludzie[1] == 1 or ludzie[1] == 0):
                ludzie[i] = 100
            elif(ludzie[1] == 2):
                ludzie[i] = 1
            timers[i] = 0
        # ktos albo przsyszedl albo wyszedl dlatego albo 2 albo 4 ludzi
        elif ludzie[i] == 3:
            if(ludzi[1] == 0):
                ludzie[i] = 101
            elif(ludzie[1] == 1):
                ludzie[i] = 2
            timers[i] = 0
        # mieszkancow jest 4 wiec 5 przyjsc nie moze
        elif ludzie[i] == 4:
            ludzie[i] -= 1
            timers[i] = 0
        # stan nie okreslony, albo 1 albo 3
        elif ludzie[i] == 100:
            # jeśli czas minął a ruchu brak to znaczy ze osoba ubyła
            if int(time.time() - timers[i]) > czas_oczekiwania_na_ruch_w_pokoju:
                ludzie[i] = 0
                timers[i] = 0
            #   jeśli czas prośby (timer) jest starszy od ruchu w pokoju i nie minął czas oczekiwania
            #   to znaczy ze osoba przybyła do tego po
            #   TODO uwzglednic kiedyś że czujnik ruchu podaje informacje jeszcze po tym jak sie wyjdzie z obszaru dodac margines bledu miedzy pomiarem z futryny a z czujnika ruchu
            elif (timers[i] < ostatni_ruch_w_pokoju[i] and
                  int(time.time()) - timers[i] < czas_oczekiwania_na_ruch_w_pokoju):
                if(ludzie[1] == 0):
                    ludzie[i] = 101
                elif(ludzie[1] == 1):
                    ludzie[1] == 2
                timers[i] = 0
        # stan nie okreslony, albo 2 albo 4
        elif ludzie[i] == 101:
            # 5 osoba nie przyjdzie bo 4 mieszkancow wiec degradujemy do stanu nieokreślonego 100
            ludzie[i] = 100
            timers[i] = 0

    # ------------------------------------------------------------------------------------------------------------------
    #   Timer z salonu
    if timers[1] != 0:
        if ludzie[1] == 0:
            if ludzie[2] == 1 or ludzie[2] == 2 or ludzie[2] == 3 or ludzie[2] == 4:
                ludzie[2] -= 1
                ludzie[1] += 1
                timers[1] = 0
            elif ludzie[2] == 100:
                if (int(time.time()) - timers[1] < czas_oczekiwania_na_ruch_w_pokoju and
                        ostatni_ruch_w_pokoju[1] > timers[1]):
                    ludzie[2] = 2
                    ludzie[1] += 1
                    timers[1] = 0
                elif int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju:
                    ludzie[2] = 0
                    ludzie[1] += 1
                    timers[1] = 0
            elif ludzie[2] == 101:
                ludzie[2] = 100
                ludzie[1] += 1
                timers[1] = 0
        elif ludzie[1] == 1:
            if ludzie[2] == 0:
                ludzie[2] = 1
                ludzie[1] -= 1
                timers[1] = 0
            elif ludzie[2] == 1 or ludzie[2] == 100:
                if (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow < timers[1]
                        and int(time.time())-timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] -= 1
                    if ludzie[2]==1:
                        ludzie[2] = 2
                    else:
                        ludzie[2] = 101
                    timers[1] = 0
                elif (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow > timers[1]
                        and int(time.time())-timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    if (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow > timers[1]
                          and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                        ludzie[1] += 1
                        ludzie[2] = 2
                        timers[1] = 0
                    if (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow < timers[1]
                          and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                        ludzie[1] += 1
                        ludzie[2] = 0
                        timers[1] = 0
            elif ludzie[2] == 2 or ludzie[2] == 3:
                if(ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow > timers[1]
                    and int(time.time())-timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] += 1
                    ludzie[2] -= 1
                    timers[1] = 0
                if(ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow < timers[1]
                    and int(time.time())-timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] -= 1
                    ludzie[2] += 1
                    timers[1] = 0
        elif ludzie[1] == 2:
            if ludzie[2] == 0:
                ludzie[1] -= 1
                ludzie[2] += 1
                timers[1] = 0
            elif ludzie[2] == 1:
                if (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow > timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] -= 1
                    ludzie[2] += 1
                    timers[1] = 0
                if (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow < timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] += 1
                    ludzie[2] -= 1
                    timers[1] = 0
            elif ludzie[2] == 2:
                ludzie[1] = 100
                ludzie[2] = 100
                timers[1] = 0
        elif ludzie[1] == 3:
            if ludzie[2] == 0:
                ludzie[1] -= 1
                ludzie[2] += 1
                timers[1] = 0
            elif ludzie[2] == 1:
                if (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow > timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] -= 1
                    ludzie[2] += 1
                    timers[1] = 0
                if (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow < timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] += 1
                    ludzie[2] -= 1
                    timers[1] = 0
        elif ludzie[1] == 4:
            ludzie[2] += 1
            ludzie[1] -= 1
            timers[1] = 0
        elif ludzie[1] == 100:
            if ludzie[2] == 0:
                if (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow > timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] = 2
                    timers[1] = 0
                    ludzie[2] += 1
                elif (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow < timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] = 0
                    timers[1] = 0
                    ludzie[2] += 1
            elif ludzie[2] == 1:
                if (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow < timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[2] -= 1
                    ludzie[1] = 101
                    timers[1] = 0
                elif (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow > timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    if (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow < timers[1]
                            and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                        ludzie[1] = 0
                        ludzie[2] = 2
                        timers[1] = 0
                    elif (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow > timers[1]
                          and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                        ludzie[1] = 2
                        ludzie[2] = 2
                        timers[1] = 0
            elif ludzie[2] == 100:
                if (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow < timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] = 0
                    ludzie[2] = 4
                    timers[1] = 0
                elif (ostatni_ruch_w_pokoju[2] - czas_wygasania_czujnikow < timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] = 4
                    ludzie[2] = 0
                    timers[1] = 0
                elif (ostatni_ruch_w_pokoju[1] - czas_wygasania_czujnikow > timers[1]
                        and int(time.time()) - timers[1] > czas_oczekiwania_na_ruch_w_pokoju):
                    ludzie[1] = 2
                    ludzie[2] = 2
                    timers[1] = 0

    # ------------------------------------------------------------------------------------------------------------------
    #   Pomocnicze timery
    if pomocnicze_timers[1] != 0:
        # ktos wyszedl z przedpokoju do salonu i w przedpokoju nikogo nie ma
        if(time.time()-ostatni_ruch_w_pokoju[2] > czas_oczekiwania_na_ruch_w_pokoju):
            if ludzie[2] == 1 :
                ludzie[2] -= 1
                pomocnicze_timers[1] = 0
            elif ludzie[2] == 100:
                ludzie[2] = 0
                pomocnicze_timers[1] = 0
        # ktos wszedl do przedpokoju z salonu a w przedpokoju nikogo nie bylo
        elif(ostatni_ruch_w_pokoju[2] > pomocnicze_timers[1] and ludzie[2] == 0):
            ludzie[2] += 1
            pomocnicze_timers[1] = 0

    # ------------------------------------------------------------------------------------------------------------------
    #   Przedpokoj
    if futryna_przedpokoj_state == "true" and not tryb_goscia:
        futryna_przedpokoj_state = False
        #   jesli ludzi 0 to +1
        if ludzie[2] == 0 and ludzie[1] != 4:
            ludzie[2] += 1
            show_house()

        #   jesli ktoś byl w pokoju to albo ubył z domu albo doszedł kolejny
        #   jeśli ruch w pokoju wykryty to znaczy ze nikt nie wyszedł a przybył
        #   jeśli mielismy 2 osoby w pokoju i przez drzwi ktoś przeszedl to albo ktos ubył albo przybyła 3 osoba
        #   wtedy system wchodzi w stan nieokreślony oznaczany cyfrą 100 oznaczający że w pokoju są albo 1 albo 3 osoby
        #   system nieokreślony stanie się określonym w momencie przejścia którejś z osób do innego pokoju
        elif ludzie[2] > 0:
            timers[2] = int(time.time())

    if ruch_przedpokoj_state == "true" and not tryb_goscia:
        ruch_przedpokoj_state = False
        ostatni_ruch_w_pokoju[2] = int(time.time())

    if futryna_salon_state == "true" and not tryb_goscia:
        futryna_salon_state = False
        timers[1] = int(time.time())

    if ruch_salon_state == "true" and not tryb_goscia:
        ruch_salon_state = False
        ostatni_ruch_w_pokoju[1] = int(time.time())


    #   zapalanie lub gaszenie swiatel
    if(ludzie[2] > 0 and swiatla[2] == False):
        swiatla[2] = True
        show_house()
    elif(ludzie[2] == 0 and swiatla[2] == True):
        swiatla[2] = False
        show_house()

    if (ludzie[1] > 0 and swiatla[1] == False):
        swiatla[1] = True
        show_house()
    elif (ludzie[1] == 0 and swiatla[1] == True):
        swiatla[1] = False
        show_house()

    if redraw_needed:
        scroll_offset = show_house()
        redraw_needed = False
    clock.tick(60)  # Ustaw 60 FPS

    if swiatla[1] != last_salon:
        last_salon = swiatla[1]
        if swiatla[1] == True:
            client.publish("salon/swiatlo/", "true", qos=2)  # Publikujemy wiadomość do tematu
        else:
            client.publish("salon/swiatlo/", "false", qos=2)  # Publikujemy wiadomość do tematu

    if swiatla[2] != last_przedpokoj:
        last_przedpokoj = swiatla[2]
        if swiatla[2] == True:
            client.publish("przedpokoj/swiatlo/", "true", qos=2)  # Publikujemy wiadomość do tematu
        else:
            client.publish("przedpokoj/swiatlo/", "false", qos=2)  # Publikujemy wiadomość do tematu

    if glowne_menu and menu_position == 0:
        show_house()
    elif menu_position == 1:
        show_settings()
    elif menu_position == 2:
        settings.parametry(screen, menu_events, czas_wygasania_state, czas_oczekiwania_state)
    elif menu_position == 3:
        menu.wychodzenie_tryb_goscia(screen, menu_events, temp_ludzie_salon, temp_ludzie_przedpokoj)

pygame.quit()
sys.exit()
