import autopy
import pyautogui
import cv2
import mediapipe as mp
import math

# Инициализация камеры
camera = cv2.VideoCapture(0)

# Получение размеров экрана
screen_width, screen_height = autopy.screen.size()

# Установка разрешения камеры в соответствии с разрешением экрана
camera.set(cv2.CAP_PROP_FRAME_WIDTH, screen_width)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, screen_height)

# Инициализация MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Переменные для сглаживания курсора
prev_x, prev_y = 0, 0
smoothening = 7  # Коэффициент сглаживания

# Порог для клика и зажатия (можно настроить)
click_threshold = 60  # В пикселях

# Порог для прокрутки (можно настроить)
scroll_threshold = 70  # Пиксели перемещения для прокрутки

# Коэффициент скорости прокрутки
scroll_speed = 5  # Увеличьте для большей скорости

# Коэффициент скорости движения мыши
mouse_speed = 8  # Увеличьте для большей скорости движения курсора

# Флаги для предотвращения множественных действий
holding = False
scrolling = False
last_scroll_y = 0

print("Запуск программы.\n Нажмите 'q' для выхода.")

while True:
    success, img = camera.read()
    if not success:
        print("Не удалось получить кадр с камеры.")
        break

    # Отражение изображения для естественности
    img = cv2.flip(img, 1)

    # Преобразование изображения в RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Обработка изображения для обнаружения рук
    results = hands.process(img_rgb)

    # Получение размеров изображения
    img_height, img_width, _ = img.shape

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Отрисовка ключевых точек руки
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Получение координат указательного пальца для движения курсора
            index_tip = hand_landmarks.landmark[8]
            index_x, index_y = int(index_tip.x * img_width), int(index_tip.y * img_height)

            # Получение координат большого и среднего пальцев для клика и зажатия
            thumb_tip = hand_landmarks.landmark[4]
            middle_tip = hand_landmarks.landmark[12]

            thumb_x, thumb_y = int(thumb_tip.x * img_width), int(thumb_tip.y * img_height)
            middle_x, middle_y = int(middle_tip.x * img_width), int(middle_tip.y * img_height)

            # Расчет расстояния между большим и средним пальцами для клика/зажатия
            distance_click = math.hypot(middle_x - thumb_x, middle_y - thumb_y)
            # Расчет расстояния между указательным и средним пальцами для прокрутки
            distance_scroll = math.hypot(middle_x - index_x, middle_y - index_y)

            # Отображение точек на изображении
            cv2.circle(img, (index_x, index_y), 10, (255, 0, 255), cv2.FILLED)    # Указательный палец
            cv2.circle(img, (thumb_x, thumb_y), 10, (0, 255, 0), cv2.FILLED)      # Большой палец
            cv2.circle(img, (middle_x, middle_y), 10, (0, 0, 255), cv2.FILLED)    # Средний палец

            # Логика для зажатия левой кнопки мыши (большой и средний пальцы)
            if distance_click < click_threshold:
                if not holding:
                    autopy.mouse.toggle(autopy.mouse.Button.LEFT, True)  # Нажатие левой кнопки
                    holding = True
                    print("Левая кнопка мыши зажата.")
                    # Визуальный индикатор зажатия
                    cv2.circle(img, ((thumb_x + middle_x) // 2, (thumb_y + middle_y) // 2), 15, (0, 255, 255), cv2.FILLED)
            else:
                if holding:
                    autopy.mouse.toggle(autopy.mouse.Button.LEFT, False)  # Отпускание левой кнопки
                    holding = False
                    print("Левая кнопка мыши отпущена.")

            # Логика для прокрутки колесика мыши (указательный и средний пальцы)
            if distance_scroll < click_threshold:
                
                if not scrolling:
                    scrolling = True
                    last_scroll_y = middle_y  # Инициализация начальной позиции для прокрутки
                    print("Режим прокрутки активирован.")
                    # Визуальный индикатор прокрутки
                    cv2.circle(img, ((index_x + middle_x) // 2, (index_y + middle_y) // 2), 15, (255, 255, 0), cv2.FILLED)
            else:
                if scrolling:
                    scrolling = False
                    print("Режим прокрутки деактивирован.")

            # Если режим прокрутки активен
            if scrolling:
                # Текущая позиция среднего пальца
                current_scroll_y = middle_y
                # Расчет разницы в вертикальном движении
                delta_y = current_scroll_y - last_scroll_y

                if abs(delta_y) > scroll_threshold:
                
                    scroll_amount = int(delta_y * scroll_speed)
                    if scroll_amount > 0:
                        # Прокрутка вниз
                        pyautogui.scroll(-scroll_amount)  # Отрицательное значение для прокрутки вниз
                    elif scroll_amount < 0:
                        # Прокрутка вверх
                        pyautogui.scroll(-scroll_amount)   # Положительное значение для прокрутки вверх
                    last_scroll_y = current_scroll_y  # Обновление последней позиции
                    

            # Если не в режиме прокрутки, управляем курсором
            if not scrolling:
                # Преобразование координат указательного пальца в масштаб экрана
                screen_x = index_x * screen_width / img_width
                screen_y = index_y * screen_height / img_height

                # Скорректированное движение курсора с учетом коэффициента mouse_speed
                curr_x = prev_x + (screen_x - prev_x) / (smoothening / mouse_speed)
                curr_y = prev_y + (screen_y - prev_y) / (smoothening / mouse_speed)

                # Перемещение курсора
                autopy.mouse.move(int(curr_x), int(curr_y))

                # Обновление предыдущих координат
                prev_x, prev_y = curr_x, curr_y

    # Отображение изображения
    cv2.imshow("Mouse Control", img)

    # Выход из цикла при нажатии 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Выход из программы.")
        break

# Освобождение ресурсов
camera.release()
cv2.destroyAllWindows()
