import os

import pyautogui
import cv2
import numpy as np
from pynput import mouse
from pprint import pprint

clicks = []
background_color = None

# Цвета фигур в игре
game_colors = {
    (178, 175, 131): 1,  # WW
    (195, 154, 147): 2,  # LN
    (198, 150, 194): 3,  # VG
    (175, 112, 169): 3,  # VG (skills)
    (115, 115, 135): 4,  # BR
    (127, 139, 210): 5,  # LH
    (147, 182, 200): 6,  # CM
    (113, 160, 160): 6,  # CM (skills)
}


def on_click(x, y, button, pressed):
    global clicks, background_color
    if pressed:
        if background_color is None:
            screenshot = pyautogui.screenshot()
            screenshot_cv = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_RGB2BGR)
            background_color = tuple(screenshot_cv[y, x])
            print(f"Цвет фона установлен как: {background_color}")
            return False
        else:
            clicks.append((x, y))
            print(f"Угловая точка {len(clicks)} установлена в: {(x, y)}")
            if len(clicks) == 2:
                return False


def exclude_color(image, target_color, tolerance):
    if image is None:
        print("Ошибка: изображение не удалось загрузить.")
        return None

    image_rgb = image
    target_color = np.array(target_color)

    # Создать маску на основе допустимого отклонения от целевого цвета
    lower_bound = target_color - tolerance
    upper_bound = target_color + tolerance
    mask = cv2.inRange(image_rgb, lower_bound, upper_bound)

    image_rgb[mask != 0] = [255, 255, 255]  # Белый цвет

    return image_rgb


def get_average_color(image):
    arr = np.array(image)

    if arr.size == 0:
        return 0, 0, 0

    average_color = arr.mean(axis=(0, 1))
    return tuple(average_color.astype(int))


def closest_color(color):
    min_distance = float('inf')
    closest = None
    for game_color, name in game_colors.items():
        distance = np.linalg.norm(np.array(color) - np.array(game_color))
        if distance < min_distance:
            min_distance = distance
            closest = game_color
    return closest


def draw_grid(image, grid_size, line_color=(0, 0, 255), line_thickness=1):
    """Рисует сетку на изображении"""
    height, width = image.shape[:2]
    grid_color = np.array(line_color)

    for i in range(1, grid_size[0]):
        x = i * width // grid_size[0]
        cv2.line(image, (x, 0), (x, height), grid_color.tolist(), line_thickness)

    for i in range(1, grid_size[1]):
        y = i * height // grid_size[1]
        cv2.line(image, (0, y), (width, y), grid_color.tolist(), line_thickness)

    return image


def create_color_map_image(colors, grid_size):
    """Создает изображение, где каждый пиксель соответствует среднему цвету клетки"""
    height, width = grid_size
    cell_width = width // len(colors[0])
    cell_height = height // len(colors)

    color_map_image = np.zeros((height, width, 3), dtype=np.uint8)

    for row in range(len(colors)):
        for col in range(len(colors[row])):
            color = colors[row][col]
            top_left = (col * cell_width, row * cell_height)
            bottom_right = ((col + 1) * cell_width, (row + 1) * cell_height)
            color_map_image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]] = color

    return color_map_image


def main():
    global background_color
    # Ввод размеров игрового поля
    width, height = 8, 8  # map(int, input("Введите размеры поля (ширина высота): ").split())

    print("Пожалуйста, кликните на цвет фона.")

    # Настраиваем прослушиватель кликов
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    if background_color is None:
        print("Цвет фона не был установлен. Завершение работы.")
        return

    print("Пожалуйста, кликните по левому верхнему углу области игрового поля, затем по правому нижнему углу.")

    # Настраиваем прослушиватель кликов
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    # Получаем координаты кликов
    (x1, y1), (x2, y2) = clicks

    # Получаем область экрана
    left = min(x1, x2)
    top = min(y1, y2)
    right = max(x1, x2)
    bottom = max(y1, y2)

    # Делам скриншот
    screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))

    # Преобразуем скриншот в формат OpenCV
    screenshot_cv = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_RGB2BGR)

    # Сохраняем скриншот в файл
    os.mkdir(os.path.join(os.getcwd(), "images"))

    screenshot_filename = "images/screenshot.png"
    cv2.imwrite(screenshot_filename, screenshot_cv)
    print(f"Скриншот сохранен в {screenshot_filename}")

    # Создаем скриншот с разметкой клеток
    grid_screenshot = draw_grid(screenshot_cv.copy(), (width, height))
    grid_screenshot_filename = "images/grid_screenshot.png"
    cv2.imwrite(grid_screenshot_filename, grid_screenshot)
    print(f"Скриншот с разметкой клеток сохранен в {grid_screenshot_filename}")

    # Размер каждой клетки
    cell_width = (right - left) // width
    cell_height = (bottom - top) // height

    print(f"Размер каждой клетки: {cell_width}x{cell_height}")

    color_matrix = []
    closest_matrix = []
    heroes_matrix = []

    print("Средний цвет каждой клетки:")

    # Обрабатываем каждую клетку
    for row in range(height):
        row_colors = []
        row_closest = []
        row_heroes = []
        for col in range(width):
            # Вычисляем координаты клетки
            cell_left = col * cell_width
            cell_top = row * cell_height
            cell_right = min(cell_left + cell_width, right)
            cell_bottom = min(cell_top + cell_height, bottom)

            # Проверяем координаты клетки
            print(
                f"Обрабатываем клетку ({row}, {col}) с координатами: ({cell_left}, {cell_top}), ({cell_right}, {cell_bottom})")

            # Извлекаем клетку из скриншота
            cell_image = screenshot_cv[cell_top:cell_bottom, cell_left:cell_right]

            # Проверяем содержимое клетки
            if cell_image.size == 0:
                print(f"Клетка ({row}, {col}) не содержит видимого содержимого")
                row_colors.append(None)
                continue

            # Сохраняем изображение клетки
            result_image = exclude_color(cell_image, background_color, tolerance=30)
            cell_filename = f"images/cell_{row}_{col}.png"
            cv2.imwrite(cell_filename, result_image)
            print(f"Изображение клетки ({row}, {col}) сохранено в {cell_filename}")

            # Получаем средний цвет клетки
            avg_color = get_average_color(result_image)
            print(f"Клетка ({row}, {col}): {avg_color}")
            row_colors.append(avg_color)

            # Приведение цвета к одному из цветов игры
            closest_game_color = closest_color(avg_color)
            print(f"Клетка ({row}, {col}) приведена к цвету {game_colors[closest_game_color]}")
            row_closest.append(closest_game_color)
            row_heroes.append(game_colors[closest_game_color])

        color_matrix.append(row_colors)
        closest_matrix.append(row_closest)
        heroes_matrix.append(row_heroes)

    # Вывод массива цветов клеток
    print("\nПолученнпое поле:")
    pprint(heroes_matrix)

    # Создаем изображение, где каждый пиксель соответствует среднему цвету клетки
    color_map_image = create_color_map_image(color_matrix, (height, width))

    # Сохраняем изображение с цветами клеток
    color_map_filename = "images/color_map.png"
    cv2.imwrite(color_map_filename, color_map_image)
    print(f"Изображение с цветами клеток сохранено в {color_map_filename}")

    # Создаем изображение, где каждый пиксель соответствует ближайшему цвету героя
    closest_map_image = create_color_map_image(closest_matrix, (height, width))

    # Сохраняем изображение с цветами клеток
    closest_map_filename = "images/closest_map.png"
    cv2.imwrite(closest_map_filename, closest_map_image)
    print(f"Изображение с приведёнными цветами клеток сохранено в {closest_map_filename}")


def get_field(screenshot, width, height, cell_width, cell_height, ):
    screenshot_cv = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_RGB2BGR)
    heroes_matrix = []

    for row in range(height):
        row_heroes = []
        for col in range(width):
            cell_left = col * cell_width
            cell_top = row * cell_height
            cell_right = cell_left + cell_width
            cell_bottom = cell_top + cell_height

            cell_image = screenshot_cv[cell_top:cell_bottom, cell_left:cell_right]

            result_image = exclude_color(cell_image, (np.uint8(65), np.uint8(53), np.uint8(47)), tolerance=30)
            avg_color = get_average_color(result_image)

            closest_game_color = closest_color(avg_color)
            row_heroes.append(game_colors[closest_game_color])

        heroes_matrix.append(row_heroes)

    return heroes_matrix


if __name__ == "__main__":
    main()
