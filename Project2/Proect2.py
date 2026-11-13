import os
import sys
import random
import math
import pygame
import tkinter as tk
from tkinter import messagebox

# --- 1. СТАРТОВОЕ ПРЕДУПРЕЖДЕНИЕ ---
def show_warning_dialog():
    root = tk.Tk()
    root.withdraw()
    response = messagebox.askyesno(
        "Системное предупреждение",
        "Приветствую, спасибо что решили установить мою мини-игру! :D\n"
        "Приятной игры, персонажи взяты из вселенной Myneosha.\n\n"
        "НЕ РЕКОМЕНДУЕТСЯ ЕСЛИ ВЫ ЭПИЛЕПТИК, ЕСТЬ ВСПЫШКИ!\n\n"
        "Переключение диалогов на ПРОБЕЛ или ENTER\n\n"
        "Запустить игру?"
    )
    root.destroy()
    return response

if not show_warning_dialog():
    sys.exit()

# --- 2. ИНИЦИАЛИЗАЦИЯ PYGAME И ОКНА ---
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Цветочки")
clock = pygame.time.Clock()

# Цвета-заглушки
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 120, 255)
PINK = (255, 120, 180)
YELLOW = (255, 220, 0)

# Шрифты
font_text = pygame.font.SysFont("courier", 20, bold=True)
font_counter = pygame.font.SysFont("courier", 24, bold=True)

def resource_path(relative_path):
    try:
        # PyInstaller создает временную папку _MEIPASS и складывает туда все файлы
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def load_image(filename, width, height, fallback_color):
    path = resource_path(filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (width, height))
        except Exception:
            pass
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(fallback_color)
    return surf

# --- 3. ЗАГРУЗКА СПРАЙТОВ И ФОНА ---
bg_surf = load_image("bg_normal.png", WIDTH, HEIGHT, BLACK) 
bg_faded_surf = load_image("bg_faded.png", WIDTH, HEIGHT, (30, 30, 30))

# Кадры ходьбы Ильи
player_walk_frames = {
    "down": [load_image(f"player_walk_down_{i}.png", 48, 48, BLUE) for i in range(1, 4)],
    "up": [load_image(f"player_walk_up_{i}.png", 48, 48, BLUE) for i in range(1, 4)],
    "left": [load_image(f"player_walk_left_{i}.png", 48, 48, BLUE) for i in range(1, 4)],
    "right": [load_image(f"player_walk_right_{i}.png", 48, 48, BLUE) for i in range(1, 4)]
}

# Кадры Леры
lera_frames = [
    load_image("lera_idle_1.png", 48, 48, PINK),
    load_image("lera_idle_2.png", 48, 48, PINK)
]

# Цветы на карте
flower_surfs = [
    load_image("map_flower_1.png", 32, 32, YELLOW),
    load_image("map_flower_2.png", 32, 32, (255, 150, 0)),
    load_image("map_flower_3.png", 32, 32, (200, 100, 255)),
    load_image("map_flower_rare.png", 32, 32, (255, 255, 255))
]

# --- 4. СЦЕНАРИЙ И ДИАЛОГИ ---
intro_dialogues = [
    "[Лера] - ...",
    "[Система] - *Вы слышите тихие всхлипы*",
    "[Илья] - *Ей так грустно... Не могу же я бросить единственного близкого мне человека.*",
    "[Илья] - *Тут в округе были цветы. Соберу ей небольшой букетик.*",
    "[Система] - Передвигайтесь на WASD. Чтобы подобрать цветок нажмите E."
]

current_dialogue_idx = 0
dialogue_active = True
char_index = 0
displayed_text = ""
text_timer = 0

# --- 5. ИГРОВЫЕ ПЕРЕМЕННЫЕ ---
player_x = WIDTH // 2 - 150
player_y = HEIGHT // 2
player_base_speed = 2.0  # Уменьшили базовую скорость вдвое

current_direction = "down"
anim_frame_index = 0
anim_speed_counter = 0

lera_x = WIDTH // 2 + 100
lera_y = HEIGHT // 2
lera_frame_index = 0
lera_anim_counter = 0

flowers = []
for _ in range(8):
    fx = random.randint(100, WIDTH - 100)
    fy = random.randint(150, HEIGHT - 100)
    f_type = random.randint(0, len(flower_surfs) - 1)
    flowers.append({"x": fx, "y": fy, "type": f_type, "collected": False})

collected_flowers_count = 0
intro_alpha = 255

# --- ФУНКЦИЯ ОТРИСОВКИ МИРА ---
def draw_scene(surface):
    current_bg = bg_faded_surf if (collected_flowers_count >= 4) else bg_surf
    surface.blit(current_bg, (0, 0))
    
    surface.blit(lera_frames[lera_frame_index], (lera_x, lera_y))
    
    for f in flowers:
        if not f["collected"]:
            surface.blit(flower_surfs[f["type"]], (f["x"], f["y"]))
            
    current_player_surf = player_walk_frames[current_direction][anim_frame_index]
    surface.blit(current_player_surf, (player_x, player_y))

# --- 6. ДИАЛОГОВОЕ ОКНО ---
def draw_dialogue_box(text):
    if not text:
        return
    txt_surface = font_text.render(text, True, WHITE)
    txt_rect = txt_surface.get_rect()
    
    box_width = max(600, txt_rect.width + 40)
    box_height = 60
    box_x, box_y = 40, 40
    
    box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    box_surf.fill((20, 20, 20, 200))
    
    screen.blit(box_surf, (box_x, box_y))
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 1)
    screen.blit(txt_surface, (box_x + 20, box_y + 18))

# --- ЗВУКОВЫЕ ФУНКЦИИ ---
def play_background_music(filename):
    path = resource_path(filename)
    if os.path.exists(path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.4)

def play_sound(filename, volume=0.6):
    """Воспроизводит звук. Громкость можно временно поднимать до 1.0 на глитчи"""
    path = resource_path(filename)
    if os.path.exists(path):
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        sound.play()

#ФИНАЛЬНАЯ СЦЕНА
def run_final_sequence(screen_surface):
    pygame.mixer.music.stop()
    play_sound("final_crash.mp3", volume=1.0)
    
    # 1. Затенение экрана
    for alpha in range(0, 255, 10):
        pygame.event.pump()
        screen_surface.fill(BLACK)
        flash = pygame.Surface((WIDTH, HEIGHT))
        flash.fill(BLACK)
        flash.set_alpha(alpha)
        screen_surface.blit(flash, (0, 0))
        pygame.display.flip()
        pygame.time.wait(30)

    #кадры финала
    f_rise = [
        load_image("final_flower_rise_1.png", 96, 96, (200, 0, 200)),
        load_image("final_flower_rise_2.png", 96, 96, (200, 0, 200)),
        load_image("final_flower_rise_3.png", 96, 96, (200, 0, 200))
    ]
    f_smile = load_image("final_flower_smile.png", 96, 96, (255, 50, 150))
    
    center_x = WIDTH // 2 - 48
    start_y = HEIGHT + 50
    target_y = HEIGHT // 2 - 48
    
    # 2. Плавный подъем цветка из темноты на 3 кадра
    for step in range(70):
        pygame.event.pump()
        screen_surface.fill(BLACK)
        
        frame_idx = (step // 25) % 3
        current_y = start_y + (target_y - start_y) * (step / 70)
        
        screen_surface.blit(f_rise[frame_idx], (center_x, current_y))
        pygame.display.flip()
        pygame.time.wait(30)
        
    # 3. Замена эмоции на улыбающийся глаз
    screen_surface.fill(BLACK)
    screen_surface.blit(f_smile, (center_x, target_y))
    pygame.display.flip()
    pygame.time.wait(1000)
    
    # 4. Удушающий монолог цветка
    monologue = [
        "[???] - Оу...?",
        "[???] - Ты ДЕЙСТВИТЕЛЬНО думал что жалкие цветочки помогут тебе?",
        "[???] - Нет.",
        "[???] - Тебе не скрытся от этого чувства у себя в груди"
    ]
    
    # Простой цикл вывода монолога с пошаговым нажатием Пробела
    for line in monologue:
        char_idx = 0
        current_line_text = ""
        while char_idx < len(line):
            pygame.event.pump()
            current_line_text += line[char_idx]
            char_idx += 1
            
            screen_surface.fill(BLACK)
            screen_surface.blit(f_smile, (center_x, target_y))
            
            # Рендер текста по центру
            txt_surf = font_text.render(current_line_text, True, WHITE)
            txt_rect = txt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
            screen_surface.blit(txt_surf, txt_rect)
            
            pygame.display.flip()
            pygame.time.wait(25)
            
        # Ждем нажатия пробела для следующей фразы
        waiting_for_click = True
        while waiting_for_click:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_SPACE or event.key == pygame.K_RETURN):
                    waiting_for_click = False

    # Создание файла на рабочем столе на память
    try:
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        with open(os.path.join(desktop, "....txt"), 'w', encoding='utf-8') as f:
            f.write("Когда долго сидишь в одиночестве... оно уже не кажется таким страшным")
    except:
        pass
        
    pygame.quit()
    sys.exit()

#ФУНКЦИИ ГЛИТЧЕЙ (СО ВЗРЫВОМ ГРОМКОСТИ ДО 1.0)
def trigger_glitch_eye(screen_surface):
    play_sound("glitch_pop.mp3", volume=1.0)  
    eye_surf = load_image("glitch_eye.png", 64, 64, (255, 0, 0))
    rx = random.randint(100, WIDTH - 164)
    ry = random.randint(100, HEIGHT - 164)
    
    start_ticks = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_ticks < 1500:
        pygame.event.pump()
        draw_scene(screen_surface)
        jx = rx + random.randint(-4, 4)
        jy = ry + random.randint(-4, 4)
        screen_surface.blit(eye_surf, (jx, jy))
        pygame.display.flip()
        pygame.time.wait(50)

def trigger_text_flash(screen_surface):
    play_sound("error_sound.mp3", volume=1.0)
    phrases = [
        "ТЫ ТОЧНО НЕ ОДИН?", "БЕССМЫСЛЕННО", 
        "ПРЕКРАТИ ЦЕПЛЯТСЯ ЗА...", "БЕСПОЛЕЗНО",
        "ОНи СМОТРЯТ", "ТЫ ОПОЗДАЛ", "ЭТО ТВОЯ ВИНА", "ТЫ ОДИН"
    ]
    start_ticks = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_ticks < 1200:
        pygame.event.pump()
        draw_scene(screen_surface)
        for _ in range(6):
            chosen_text = random.choice(phrases)
            glow_surf = font_counter.render(chosen_text, True, (80, 0, 0))
            text_surf = font_counter.render(chosen_text, True, (255, 30, 30))
            rx = random.randint(50, WIDTH - 500)
            ry = random.randint(50, HEIGHT - 100)
            screen_surface.blit(glow_surf, (rx + 2, ry + 2))
            screen_surface.blit(text_surf, (rx, ry))
        pygame.display.flip()
        pygame.time.wait(100)

def trigger_analog_bars(screen_surface):
    play_sound("white_noise.mp3", volume=1.0)
    start_ticks = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_ticks < 1000:
        pygame.event.pump()
        draw_scene(screen_surface)
        for _ in range(8):
            y = random.randint(0, HEIGHT - 30)
            h = random.randint(4, 25)
            color = random.choice([
                (0, 255, 100), (255, 0, 50), (0, 150, 255), (255, 255, 255)
            ])
            bar_surf = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
            bar_surf.fill((*color, 160))
            screen_surface.blit(bar_surf, (0, y))
        pygame.display.flip()
        pygame.time.wait(80)

def trigger_multi_eyes(screen_surface):
    play_sound("glitch_pop.mp3", volume=1.0)
    small_eye = load_image("glitch_eye.png", 32, 32, (180, 0, 0))
    eyes_list = []
    start_ticks = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_ticks < 2000:
        pygame.event.pump()
        if random.random() < 0.4 and len(eyes_list) < 25:
            eyes_list.append((random.randint(50, WIDTH - 80), random.randint(50, HEIGHT - 80)))
        draw_scene(screen_surface)
        for ex, ey in eyes_list:
            screen_surface.blit(small_eye, (ex, ey))
        pygame.display.flip()
        pygame.time.wait(70)

def trigger_screen_crack(screen_surface):
    play_sound("glitch_screech.mp3", volume=1.0)
    crack_surf = load_image("screen_crack.png", WIDTH, HEIGHT, (0, 0, 0, 0))
    start_ticks = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_ticks < 1500:
        pygame.event.pump()
        draw_scene(screen_surface)
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)
        screen_surface.blit(crack_surf, (offset_x, offset_y))
        pygame.display.flip()
        pygame.time.wait(60)

def trigger_phantom_lera(screen_surface):
    play_sound("glitch_pop.mp3", volume=1.0)
    phantom_surf = lera_frames[0].copy()
    phantom_surf.set_alpha(150)
    px = lera_x + random.randint(-150, 150)
    py = lera_y + random.randint(-100, 100)
    start_ticks = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_ticks < 800:
        pygame.event.pump()
        draw_scene(screen_surface)
        screen_surface.blit(phantom_surf, (px, py))
        pygame.display.flip()
        pygame.time.wait(80)

def trigger_ui_glitch(screen_surface):
    play_sound("error_sound.mp3", volume=1.0)
    start_ticks = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_ticks < 600:
        pygame.event.pump()
        draw_scene(screen_surface)
        glitch_counter = font_counter.render(f"[{collected_flowers_count}/8]??", True, (0, 255, 100))
        screen_surface.blit(glitch_counter, (WIDTH - 120 + random.randint(-20, 20), 30 + random.randint(-10, 10)))
        pygame.display.flip()
        pygame.time.wait(60)

# --- 7. ГЛАВНЫЙ ИГРОВОЙ ЦИКЛ ---
running = True
while running:
    lera_anim_counter += 1
    if lera_anim_counter >= 30:
        lera_frame_index = 1 - lera_frame_index
        lera_anim_counter = 0

    draw_scene(screen)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            # ДЭБАГ-КНОПКИ (1-7, а также 8 для быстрой проверки финала!)
            if event.key == pygame.K_1: trigger_glitch_eye(screen)
            elif event.key == pygame.K_2: trigger_text_flash(screen)
            elif event.key == pygame.K_3: trigger_analog_bars(screen)
            elif event.key == pygame.K_4: trigger_multi_eyes(screen)
            elif event.key == pygame.K_5: trigger_screen_crack(screen)
            elif event.key == pygame.K_6: trigger_phantom_lera(screen)
            elif event.key == pygame.K_7: trigger_ui_glitch(screen)
            elif event.key == pygame.K_8: run_final_sequence(screen) # Тест финала
                
            if dialogue_active and (event.key == pygame.K_SPACE or event.key == pygame.K_RETURN):
                if char_index < len(intro_dialogues[current_dialogue_idx]):
                    displayed_text = intro_dialogues[current_dialogue_idx]
                    char_index = len(displayed_text)
                else:
                    current_dialogue_idx += 1
                    if current_dialogue_idx >= len(intro_dialogues):
                        dialogue_active = False
                        play_background_music("ambient_melancholy.mp3")
                    else:
                        displayed_text = ""
                        char_index = 0
                        
            # Сбор цветов на клавишу E
            if not dialogue_active and event.key == pygame.K_e:
                for f in flowers:
                    if not f["collected"]:
                        dist = math.hypot(player_x - f["x"], player_y - f["y"])
                        if dist < 60:
                            f["collected"] = True
                            collected_flowers_count += 1
                            play_sound("flower_pick.mp3", volume=0.6)
                            print(f"Цветок собран! Всего: {collected_flowers_count}/8")
                            
                            # Смена музыки на 4-м цветке
                            if collected_flowers_count == 4:
                                play_background_music("ambient_distorted.mp3")
                            
                            # ПРОВЕРКА НА ФИНАЛ (8-й цветок)
                            if collected_flowers_count == 8:
                                run_final_sequence(screen)
                            
                            # Глитчи (с 4-го по 7-й цветок)
                            elif collected_flowers_count >= 4:
                                glitch_choice = random.choice([
                                    trigger_glitch_eye, trigger_text_flash, 
                                    trigger_analog_bars, trigger_multi_eyes,
                                    trigger_screen_crack, trigger_phantom_lera, 
                                    trigger_ui_glitch
                                ])
                                glitch_choice(screen)
                            break

    # Расчет замедления игрока: после 4 цветка скорость падает с каждым новым цветком
    if not dialogue_active:
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        is_moving = False
        
        # Прогрессивное замедление (каждый цветок после 3-го забирает 0.25 скорости)
        speed_penalty = max(0, (collected_flowers_count - 3) * 0.25) if collected_flowers_count >= 4 else 0
        current_speed = max(0.5, player_base_speed - speed_penalty)
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -current_speed
            current_direction = "up"
            is_moving = True
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = current_speed
            current_direction = "down"
            is_moving = True
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -current_speed
            current_direction = "left"
            is_moving = True
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = current_speed
            current_direction = "right"
            is_moving = True
            
        player_x = max(50, min(WIDTH - 100, player_x + dx))
        player_y = max(100, min(HEIGHT - 100, player_y + dy))

        if is_moving:
            anim_speed_counter += 1
            if anim_speed_counter >= 12:  # Чуть медленнее смена кадров при ходьбе
                anim_frame_index = (anim_frame_index + 1) % 3
                anim_speed_counter = 0
        else:
            anim_frame_index = 0

    if dialogue_active and current_dialogue_idx < len(intro_dialogues):
        target_text = intro_dialogues[current_dialogue_idx]
        if char_index < len(target_text):
            text_timer += 1
            if text_timer >= 2:
                displayed_text += target_text[char_index]
                char_index += 1
                text_timer = 0

    if not dialogue_active:
        counter_text = font_counter.render(f"[{collected_flowers_count}/8]", True, WHITE)
        screen.blit(counter_text, (WIDTH - 120, 30))

    if dialogue_active:
        draw_dialogue_box(displayed_text)

    if intro_alpha > 0:
        flash_surface = pygame.Surface((WIDTH, HEIGHT))
        flash_surface.fill(WHITE)
        flash_surface.set_alpha(intro_alpha)
        screen.blit(flash_surface, (0, 0))
        intro_alpha -= 4

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
