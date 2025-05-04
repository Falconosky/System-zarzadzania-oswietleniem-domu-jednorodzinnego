import pygame
import scripts

screen = None
menu_events = None
menu_position = None

def show_settings(screen, events_list, input_state):
    screen.fill((0, 0, 0))

    """
    input_state to dict z kluczami:
      'text': aktualny wpis (string),
      'active': bool czy pole jest aktywne,
      'error': opcjonalny komunikat błędu,
      'logged_in': bool,
    """

    # --- Strzałka 'back' ---
    back_img = pygame.image.load("img/icons/arrow.png").convert_alpha()
    back_rect = back_img.get_rect(topleft=(20, 20))
    screen.blit(back_img, back_rect)
    events_list.append({"name": "back", "rect": back_rect})

    # --- Tytuł ---
    font_title = pygame.font.SysFont(None, 48)
    title_surf = font_title.render("Wpisz hasło", True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 100))
    screen.blit(title_surf, title_rect)

    # --- Pole tekstowe ---
    box_w, box_h = 400, 50
    box_x = screen.get_width() // 2 - box_w // 2
    box_y = title_rect.bottom + 20
    input_rect = pygame.Rect(box_x, box_y, box_w, box_h)
    if input_state.get('active'):
        border_color = (255, 255, 255)  # jasna ramka (aktywny)
        fill_color = (50, 50, 50)  # lekko jaśniejsze tło
    else:
        border_color = (120, 120, 120)  # ciemniejsza ramka (nieaktywny)
        fill_color = (30, 30, 30)  # ciemniejsze tło
    pygame.draw.rect(screen, fill_color, input_rect)  # Tło pola
    pygame.draw.rect(screen, border_color, input_rect, 2)  # Ramka pola
    events_list.append({"name": "password", "rect": input_rect})

    # --- Maskowany tekst (gwiazdki) ---
    display_text = "*" * len(input_state['text'])
    font_input = pygame.font.SysFont(None, 36)
    txt_surf = font_input.render(display_text, True, (255, 255, 255))
    txt_rect = txt_surf.get_rect(midleft=(box_x + 10, box_y + box_h // 2))
    screen.blit(txt_surf, txt_rect)

    # --- Komunikat błędu ---
    if input_state.get('error'):
        err_surf = font_input.render(input_state['error'], True, (255, 50, 50))
        err_rect = err_surf.get_rect(center=(screen.get_width() // 2, box_y + box_h + 30))
        screen.blit(err_surf, err_rect)

    pygame.display.flip()

def parametry(screen, menu_events, czas_wygasania_state, czas_oczekiwania_state):
    # label_surf = font_label.render("Czas jaki czeka system na informacje od czujników ruchu przed podjęciem "
    #                                "decyzji o zgaszeniu/ zapaleniu świoatła", True, (255, 255, 255))

    czas_wygasania_text = czas_wygasania_state['text']
    czas_oczekiwania_text = czas_oczekiwania_state['text']

    menu_events.clear()
    screen.fill((0, 0, 0))

    back_img = pygame.image.load("img/icons/arrow.png").convert_alpha()
    back_rect = back_img.get_rect(topleft=(20, 20))
    screen.blit(back_img, back_rect)
    menu_events.append({"name": "back", "rect": back_rect})

    save_img = pygame.image.load("img/icons/disk.png").convert_alpha()
    save_rect = save_img.get_rect(topright=(screen.get_width()-20, 20))
    screen.blit(save_img, save_rect)
    menu_events.append({"name": "save", "rect": save_rect})

    font_label = pygame.font.SysFont(None, 36)
    font_input = pygame.font.SysFont(None, 36)

    # Pole 1
    label1_surf = font_label.render("Czas oczekiwania na ruch (s):", True, (255, 255, 255))
    label1_rect = label1_surf.get_rect(center=(screen.get_width()//2, 120))
    screen.blit(label1_surf, label1_rect)

    input1_rect = pygame.Rect(label1_rect.left, label1_rect.bottom + 10, label1_rect.width, 50)
    fill1 = (50, 50, 50) if czas_oczekiwania_state['active'] else (30, 30, 30)
    border1 = (255, 255, 255) if czas_oczekiwania_state['active'] else (120, 120, 120)
    pygame.draw.rect(screen, fill1, input1_rect)
    pygame.draw.rect(screen, border1, input1_rect, 2)
    text1_surf = font_input.render(czas_oczekiwania_text, True, (255, 255, 255))
    screen.blit(text1_surf, text1_surf.get_rect(midleft=(input1_rect.left + 10, input1_rect.centery)))
    menu_events.append({"name": "czas_oczekiwania", "rect": input1_rect})

    # Pole 2
    label2_surf = font_label.render("Czas wygasania czujników (s):", True, (255, 255, 255))
    label2_rect = label2_surf.get_rect(center=(screen.get_width()//2, 230))
    screen.blit(label2_surf, label2_rect)

    input2_rect = pygame.Rect(label2_rect.left, label2_rect.bottom + 10, label2_rect.width, 50)
    fill2 = (50, 50, 50) if czas_wygasania_state['active'] else (30, 30, 30)
    border2 = (255, 255, 255) if czas_wygasania_state['active'] else (120, 120, 120)
    pygame.draw.rect(screen, fill2, input2_rect)
    pygame.draw.rect(screen, border2, input2_rect, 2)
    text2_surf = font_input.render(czas_wygasania_text, True, (255, 255, 255))
    screen.blit(text2_surf, text2_surf.get_rect(midleft=(input2_rect.left + 10, input2_rect.centery)))
    menu_events.append({"name": "czas_wygasania", "rect": input2_rect})

    pygame.display.flip()

def handle_login_event(event, input_state, czas_wygasania_state, czas_oczekiwania_state):
    global menu_position
    """
    event: pygame event
    input_state: ten sam obiekt, modyfikowany in place
    """
    # Jeśli pole aktywne, zbieramy TEXTINPUT / backspace / enter
    if input_state['active']:
        if event.type == pygame.TEXTINPUT:
            input_state['text'] += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                input_state['text'] = input_state['text'][:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Porównujemy hash
                hash_input = input_state['text']
                stored_hash = scripts.get_config_value("login_password_hash") or ""
                if hash_input == stored_hash:
                    input_state['logged_in'] = True
                    input_state['error'] = None
                else:
                    input_state['error'] = "Niepoprawne hasło"
                # Po enter wyłączamy text input
                pygame.key.stop_text_input()
                input_state['active'] = False
    if czas_wygasania_state['active']:
        if event.type == pygame.TEXTINPUT:
            czas_wygasania_state['text'] += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                czas_wygasania_state['text'] = czas_wygasania_state['text'][:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Po enter wyłączamy text input
                pygame.key.stop_text_input()
                czas_wygasania_state['active'] = False
    if czas_oczekiwania_state['active']:
        if event.type == pygame.TEXTINPUT:
            czas_oczekiwania_state['text'] += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                czas_oczekiwania_state['text'] = czas_oczekiwania_state['text'][:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Po enter wyłączamy text input
                pygame.key.stop_text_input()
                czas_oczekiwania_state['active'] = False