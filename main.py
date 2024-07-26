import sys
import time

import pyautogui
from art import text2art
from pynput import mouse

from color_analyzer import get_field

clicks = []


def on_click(x, y, button, pressed):
    global clicks
    if pressed:
        clicks.append((x, y))
        print(f"Угловая точка {len(clicks)} установлена в: {(x, y)}")
        if len(clicks) == 2:
            return False


def find_combinations(grid):
    rows, cols = len(grid), len(grid[0])
    max_combo = 0
    place = (0, 0)

    def check_horizontal(row, col):
        value = grid[row][col]
        count = 1
        for c in range(col + 1, cols):
            if grid[row][c] == value:
                count += 1
            else:
                break
        return count

    def check_vertical(row, col):
        value = grid[row][col]
        count = 1
        for r in range(row + 1, rows):
            if grid[r][col] == value:
                count += 1
            else:
                break
        return count

    def check_corner(row, col):
        value = grid[row][col]
        if row + 2 < rows and col + 2 < cols:
            if (grid[row][col + 1] == value and grid[row][col + 2] == value and
                    grid[row + 1][col] == value and grid[row + 2][col] == value):
                return 5
        if row - 2 >= 0 and col + 2 < cols:
            if (grid[row][col + 1] == value and grid[row][col + 2] == value and
                    grid[row - 1][col] == value and grid[row - 2][col] == value):
                return 5
        if row + 2 < rows and col - 2 >= 0:
            if (grid[row][col - 1] == value and grid[row][col - 2] == value and
                    grid[row + 1][col] == value and grid[row + 2][col] == value):
                return 5
        if row - 2 >= 0 and col - 2 >= 0:
            if (grid[row][col - 1] == value and grid[row][col - 2] == value and
                    grid[row - 1][col] == value and grid[row - 2][col] == value):
                return 5
        return 1

    for r in range(rows - 1):
        for c in range(cols - 1):
            if grid[r][c] == grid[r][c + 1]:
                count = check_horizontal(r, c)
                if count > max_combo:
                    max_combo = count
                    place = (r, c + 1)
            if grid[r][c] == grid[r + 1][c]:
                count = check_vertical(r, c)
                if count > max_combo:
                    max_combo = count
                    place = (r + 1, c)
            count = check_corner(r, c)
            if count > max_combo:
                max_combo = count
                place = (r, c)

    return max_combo, place


def best_move(grid):
    rows, cols = len(grid), len(grid[0])
    best_cells_count = -1
    best_move = None

    def swap_and_check(r1, c1, r2, c2):
        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
        cells_count, _ = find_combinations(grid)
        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
        return cells_count

    for r in range(rows - 1, -1, -1):
        for c in range(cols - 1, -1, -1):
            if c - 1 >= 0:
                cells_count = swap_and_check(r, c, r, c - 1)
                if cells_count > best_cells_count:
                    best_cells_count = cells_count
                    best_move = ((r, c), (r, c - 1))
            if r - 1 >= 0:
                cells_count = swap_and_check(r, c, r - 1, c)
                if cells_count > best_cells_count:
                    best_cells_count = cells_count
                    best_move = ((r, c), (r - 1, c))

    return best_move, best_cells_count


def perform_move(move, top_left, cell_size):
    (row1, col1), (row2, col2) = move
    x1 = top_left[0] + col1 * cell_size + cell_size // 4 * 3
    y1 = top_left[1] + row1 * cell_size + cell_size // 4 * 3

    if row1 == row2:
        y2 = y1
        x2 = x1 - cell_size * 2
    else:
        x2 = x1
        y2 = y1 - cell_size * 2

    pyautogui.moveTo(x1, y1)
    pyautogui.dragTo(x2, y2, duration=0.2)


def init():
    ascii_label = text2art('Dragon Chess Bot')
    print(ascii_label)
    print('[v1.0]')
    print('Нажмите сначала в левый верхний угол игровой области, затем в правый нижний угол игровой области.')
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()


def calc_area():
    global clicks
    width, height = 8, 8
    (x1, y1), (x2, y2) = clicks
    left = min(x1, x2)
    top = min(y1, y2)
    right = max(x1, x2)
    bottom = max(y1, y2)
    cell_width = (right - left) // width
    cell_height = (bottom - top) // height
    return left, top, right, bottom, width, height, cell_width, cell_height


def calc_move(left, top, right, bottom, width, height, cell_width, cell_height):
    screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
    field = get_field(screenshot, width, height, cell_width, cell_height)
    combo, place = find_combinations(field)
    if combo >= 3:
        field[place[0]][place[1]] = -1
    move, count = best_move(field)
    if 2 < count < 6:
        print(f'Лучший ход: {move}, {count} в ряд')
        if move:
            perform_move(move, (left, top), cell_width)
    elif count >= 6:
        print('Ожидание поля')
    else:
        print('Ход не найден, сделайте ход вручную')
    time.sleep(0.5)


def main():
    try:
        init()
        area = calc_area()
        while True:
            calc_move(*area)
    except Exception as e:
        input(f"Произошла ошибка: {e}.\nПопробуйте перезапустить программу и выбрать правильную область игры.")


if __name__ == '__main__':
    main()
