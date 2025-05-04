import pygame, math
import scripts

def show_menu(screen, scroll_offset=0, start_x=0, start_y=0, events_list=None, tryb_goscia = False):
    ile_kafelkow = 3
    # z racji na to ze namieszałem nazewnictwo polskie z angielskim to pozwole sobie na śmieszne nazwy zmiennych
    starting_index_normal_kafelkas = 0
    if(scripts.get_config_value("debug") == "1"):
        ile_kafelkow += 4


    margin = 20
    tile_area_width = screen.get_width() // 2 - 10
    kafelki_size = (tile_area_width - margin * 5) / 3

    # Obliczamy liczbę wierszy i łączną wysokość menu
    n_rows = math.ceil(ile_kafelkow / 3)
    menu_total_height = margin + (n_rows - 1) * (kafelki_size + margin) + kafelki_size

    # Dolny limit – jeśli menu jest wyższe niż ekran, nie możemy przesunąć offsetu wyżej niż 0,
    # a na dole (najmniejsza wartość) nie możemy przekroczyć: ekran.get_height() - menu_total_height.
    min_scroll_offset = min(0, screen.get_height() - menu_total_height)
    # Przycinamy scroll_offset do przedziału [min_scroll_offset, 0]
    clamped_scroll_offset = max(min_scroll_offset, min(scroll_offset, 0))

    # Nadpisujemy scroll_offset wartością przyciętą
    scroll_offset = clamped_scroll_offset

    font = pygame.font.SysFont(None, 50)
    scale_factor = 0.3
    new_width = int(kafelki_size * scale_factor)
    new_height = int(kafelki_size * scale_factor)

    screen_rect = screen.get_rect()

    # Rysujemy kafelki z uwzględnieniem scroll_offset
    for i in range(ile_kafelkow):
        col = i % 3
        row = i // 3
        x = start_x + margin + (kafelki_size + margin) * col
        y = start_y + scroll_offset + margin + (kafelki_size + margin) * row
        tile_rect = pygame.Rect(x, y, kafelki_size, kafelki_size)
        pygame.draw.rect(screen, (140, 140, 140), (x, y, kafelki_size, kafelki_size))

        img = None
        line1 = ""
        line2 = ""
        event = None

        if scripts.get_config_value("debug") == "1" and i < 4:
            if i - starting_index_normal_kafelkas == 0:
                img = pygame.image.load("img/icons/door.png").convert_alpha()
                line1 = font.render("[D] Funtryna", True, (0, 0, 0))
                line2 = font.render("Przedpokoj", True, (0, 0, 0))
                event = {"tile_index": i, "name": "futryna_przedpokoj", "rect": tile_rect}
            if i - starting_index_normal_kafelkas == 1:
                img = pygame.image.load("img/icons/door.png").convert_alpha()
                line1 = font.render("[D] Funtryna", True, (0, 0, 0))
                line2 = font.render("Salon", True, (0, 0, 0))
                event = {"tile_index": i, "name": "futryna_salon", "rect": tile_rect}
            if i - starting_index_normal_kafelkas == 2:
                img = pygame.image.load("img/icons/walking.png").convert_alpha()
                line1 = font.render("[D] Ruch", True, (0, 0, 0))
                line2 = font.render("Przedpokoj", True, (0, 0, 0))
                event = {"tile_index": i, "name": "ruch_przedpokoj", "rect": tile_rect}
            if i - starting_index_normal_kafelkas == 3:
                img = pygame.image.load("img/icons/walking.png").convert_alpha()
                line1 = font.render("[D] Ruch", True, (0, 0, 0))
                line2 = font.render("Salon", True, (0, 0, 0))
                event = {"tile_index": i, "name": "ruch_salon", "rect": tile_rect}
                starting_index_normal_kafelkas += 4
        else:
            # if i - starting_index_normal_kafelkas == 0:
            #     print("")
            if i == ile_kafelkow-3:
                img = pygame.image.load("img/icons/users.png").convert_alpha()
                line1 = None
                if not tryb_goscia:
                    line1 = font.render("Włącz tryb", True, (0, 0, 0))
                else:
                    line1 = font.render("Wyłącz tryb", True, (0, 0, 0))
                    pygame.draw.rect(screen, (89, 255, 114), (x, y, kafelki_size, kafelki_size))
                line2 = font.render("gościa", True, (0, 0, 0))
                event = {"tile_index": i, "name": "tryb_goscia", "rect": tile_rect}
            if i == ile_kafelkow - 2:
                img = pygame.image.load("img/icons/settings.png").convert_alpha()
                line1 = font.render("Ustawienia", True, (0, 0, 0))
                line2 = font.render("", True, (0, 0, 0))
                event = {"tile_index": i, "name": "settings", "rect": tile_rect}
            if i == ile_kafelkow-1:
                img = pygame.image.load("img/icons/cross.png").convert_alpha()
                line1 = font.render("wyjście do", True, (0, 0, 0))
                line2 = font.render("pulpitu", True, (0, 0, 0))
                event = {"tile_index": i, "name": "exit", "rect": tile_rect}

        if img is not None:
            img = pygame.transform.scale(img, (new_width, new_height))
            # Wycentruj obrazek w kafelku
            img_x = x + (kafelki_size - new_width) / 2
            img_y = y + (kafelki_size - new_height) / 2 - (kafelki_size * 0.1)
            screen.blit(img, (img_x, img_y))

            # Pozycja tekstu: wycentrowany w dolnej części kafelka
            line1_rect = line1.get_rect(
                center=(x + kafelki_size / 2, img_y + new_height + margin * 2))
            line2_rect = line2.get_rect(
                center=(x + kafelki_size / 2, line1_rect.bottom + margin))
            screen.blit(line1, line1_rect)
            screen.blit(line2, line2_rect)

        # Dodajemy event tylko jeśli kafelek jest widoczny na ekranie
        if events_list is not None and tile_rect.colliderect(screen_rect) and event is not None and event.get("name"):
            events_list.append(event)

    pygame.display.flip()
    # Zwracamy nowy, przycięty offset, żeby główna pętla mogła zaktualizować globalną wartość
    return scroll_offset

def wychodzenie_tryb_goscia(screen, menu_events, temp_ludzie_salon, temp_ludzie_przedpokoj):
    menu_events.clear()
    screen.fill((0, 0, 0))

    back_img = pygame.image.load("img/icons/arrow.png").convert_alpha()
    back_rect = back_img.get_rect(topleft=(20, 20))
    screen.blit(back_img, back_rect)
    menu_events.append({"name": "back", "rect": back_rect})

    back_img = pygame.image.load("img/icons/check.png").convert_alpha()
    back_rect = back_img.get_rect(topright=(screen.get_width()-20, 20))
    screen.blit(back_img, back_rect)
    menu_events.append({"name": "check", "rect": back_rect})

    y_pos = 150

    font_label = pygame.font.SysFont(None, 72)
    label1_surf = font_label.render("Wychodzisz z trybu gościa", True, (255, 255, 255))
    label1_rect = label1_surf.get_rect(center=(screen.get_width() // 2, y_pos))
    screen.blit(label1_surf, label1_rect)
    y_pos += label1_rect.height + 30
    label1_surf = font_label.render("Określ liczbe osób w pomieszczeniach", True,
                                    (255, 255, 255))
    label1_rect = label1_surf.get_rect(center=(screen.get_width() // 2, y_pos))
    screen.blit(label1_surf, label1_rect)
    y_pos += label1_rect.height + 120

    label1_surf = font_label.render("Salon", True,
                                    (255, 255, 255))
    label1_rect = label1_surf.get_rect(center=(screen.get_width() // 2, y_pos))
    screen.blit(label1_surf, label1_rect)
    y_pos += label1_rect.height + 60

    # Ustawienia pozycji
    icon_size = 72  # lub zależnie od rzeczywistego rozmiaru obrazka
    spacing = 60  # odstęp między przyciskami
    center_x = screen.get_width() // 2

    # Minus
    minus_img = pygame.image.load("img/icons/minus.png").convert_alpha()
    minus_rect = minus_img.get_rect(center=(center_x - icon_size - spacing, y_pos))
    screen.blit(minus_img, minus_rect)
    menu_events.append({"name": "salon_minus", "rect": minus_rect})

    # Liczba
    liczba_surf = font_label.render(str(temp_ludzie_salon), True, (255, 255, 255))
    liczba_rect = liczba_surf.get_rect(center=(center_x, y_pos))
    screen.blit(liczba_surf, liczba_rect)

    # Plus
    plus_img = pygame.image.load("img/icons/plus.png").convert_alpha()
    plus_rect = plus_img.get_rect(center=(center_x + icon_size + spacing, y_pos))
    screen.blit(plus_img, plus_rect)
    menu_events.append({"name": "salon_plus", "rect": plus_rect})

    y_pos += liczba_rect.height + 120
    label1_surf = font_label.render("Przedpokoj", True,
                                    (255, 255, 255))
    label1_rect = label1_surf.get_rect(center=(screen.get_width() // 2, y_pos))
    screen.blit(label1_surf, label1_rect)
    y_pos += label1_rect.height + 60

    # Ustawienia pozycji
    icon_size = 72  # lub zależnie od rzeczywistego rozmiaru obrazka
    spacing = 60  # odstęp między przyciskami
    center_x = screen.get_width() // 2

    # Minus
    minus_img = pygame.image.load("img/icons/minus.png").convert_alpha()
    minus_rect = minus_img.get_rect(center=(center_x - icon_size - spacing, y_pos))
    screen.blit(minus_img, minus_rect)
    menu_events.append({"name": "przedpokoj_minus", "rect": minus_rect})

    # Liczba
    liczba_surf = font_label.render(str(temp_ludzie_przedpokoj), True, (255, 255, 255))
    liczba_rect = liczba_surf.get_rect(center=(center_x, y_pos))
    screen.blit(liczba_surf, liczba_rect)

    # Plus
    plus_img = pygame.image.load("img/icons/plus.png").convert_alpha()
    plus_rect = plus_img.get_rect(center=(center_x + icon_size + spacing, y_pos))
    screen.blit(plus_img, plus_rect)
    menu_events.append({"name": "przedpokoj_plus", "rect": plus_rect})

    pygame.display.flip()