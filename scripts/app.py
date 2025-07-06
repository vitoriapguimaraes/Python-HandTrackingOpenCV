import cv2
import mediapipe as mp
import os
import numpy as np
from time import sleep
from pynput.keyboard import Controller, Key

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
LIGHT_BLUE = (255, 255, 0)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands()

cap = cv2.VideoCapture(0)
RES_X = 1280
RES_Y = 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, RES_X)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RES_Y)
FONT = cv2.FONT_HERSHEY_DUPLEX
word_open = False
firefox_open = False
excel_open = False
FINGER_1 = [False, True, False, False, False]
FINGER_1_2 = [False, True, True, False, False]
FINGER_1_2_3 = [False, True, True, True, False]
FINGER_1_4 = [False, True, False, False, True]
FINGER_4 = [False, False, False, False, True]
FINGER_0 = [True, False, False, False, False]
FINGER_NONE = [False, False, False, False, False]
FINGER_ALL = [True, True, True, True, True]
KEYS = [
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'O', 'P'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'K', 'L'],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'M', ',', '.', ';']
]
OFFSET = 80
BTN_SIZE = 50
key_delay = 0
text = ">"
keyboard = Controller()
draw_board = np.ones((RES_Y, RES_X, 3), np.uint8) * 255
brush_color = BLUE
brush_thickness = 1
last_x, last_y = 0, 0

INSTRUCTION = (
    """
    *Type text*:\n
        Use right hand. Touch virtual keys with index finger to type.\n
        To erase, raise only the right pinky.\n
    *Open apps* (left hand):\n
            - Index up: open Word\n
            - Index and middle up: open Excel\n
            - Index, middle, ring up: open Firefox\n
            - All fingers down: close Firefox\n
    *Draw* (two hands):\n
        Left hand sets brush color:\n
            - 1 finger up: blue\n
            - 2 up: green\n
            - 3 up: red\n
            - 4 up: eraser\n
            - All down: clear board\n
        Right hand draws with index.\n
        Right hand distance to camera changes brush thickness.
    """
)

def get_hand_landmarks(img, flip_side=False):
    """Detect hand landmarks and return their coordinates and side."""
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    all_hands = []
    if result.multi_hand_landmarks:
        for hand_side, hand_landmarks in zip(result.multi_handedness, result.multi_hand_landmarks):
            hand_info = {}
            coords = []
            for lm in hand_landmarks.landmark:
                x, y, z = int(lm.x * RES_X), int(lm.y * RES_Y), int(lm.z * RES_X)
                coords.append((x, y, z))
            hand_info['coords'] = coords
            if flip_side:
                hand_info['side'] = 'Right' if hand_side.classification[0].label == 'Left' else 'Left'
            else:
                hand_info['side'] = hand_side.classification[0].label
            all_hands.append(hand_info)
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    return img, all_hands

def fingers_up(hand):
    """Return a list indicating which fingers are up."""
    fingers = []
    if hand['side'] == 'Right':
        fingers.append(hand['coords'][4][0] < hand['coords'][3][0])
    else:
        fingers.append(hand['coords'][4][0] > hand['coords'][3][0])
    for tip in [8, 12, 16, 20]:
        fingers.append(hand['coords'][tip][1] < hand['coords'][tip - 2][1])
    return fingers

def draw_button(img, pos, key, size=50, rect_color=WHITE):
    """Draw a virtual keyboard button."""
    cv2.rectangle(img, pos, (pos[0] + size, pos[1] + size), rect_color, cv2.FILLED)
    cv2.rectangle(img, pos, (pos[0] + size, pos[1] + size), BLUE, 1)
    cv2.putText(img, key, (pos[0] + 15, pos[1] + 30), FONT, 1, BLACK, 2)
    return img

while True:
    ret, img = cap.read()
    img = cv2.flip(img, 1)
    img, all_hands = get_hand_landmarks(img)

    tip = "Raise right hand's fingers for instructions. Press 'ESC' to exit."
    x_tip, y_tip, w_tip, h_tip = 0, 0, RES_X, 30
    cv2.rectangle(img, (x_tip, y_tip), (x_tip + w_tip, y_tip + h_tip), WHITE, cv2.FILLED)
    cv2.rectangle(img, (x_tip, y_tip), (x_tip + w_tip, y_tip + h_tip), BLUE, 1)
    cv2.putText(img, tip, (x_tip + 5, y_tip + 20), FONT, 0.6, BLACK, 1)

    if len(all_hands) == 1:
        hand1_fingers = fingers_up(all_hands[0])
        if all_hands[0]['side'] == 'Right':
            idx_x, idx_y, idx_z = all_hands[0]['coords'][8]
            cv2.putText(img, f"Press on -65 or lower", (850, 105), FONT, 0.6, BLACK, 1)
            cv2.putText(img, f"Distance: {idx_z}", (850, 130), FONT, 0.6, BLACK, 1)
            for row_idx, row in enumerate(KEYS):
                for col_idx, key in enumerate(row):
                    key_disp = key.lower() if sum(hand1_fingers) <= 1 else key
                    img = draw_button(img, (OFFSET + col_idx * (BTN_SIZE + 30), OFFSET + row_idx * (BTN_SIZE + 30)), key_disp)
                    if (OFFSET + col_idx * 80) < idx_x < (100 + col_idx * 80) and (OFFSET + row_idx * 80) < idx_y < (100 + row_idx * 80):
                        img = draw_button(img, (OFFSET + col_idx * (BTN_SIZE + 30), OFFSET + row_idx * (BTN_SIZE + 30)), key_disp, rect_color=GREEN)
                        if idx_z < -65:
                            key_delay = 1
                            key_to_type = key_disp
                            img = draw_button(img, (OFFSET + col_idx * (BTN_SIZE + 30), OFFSET + row_idx * (BTN_SIZE + 30)), key_disp, rect_color=LIGHT_BLUE)
            if key_delay:
                key_delay += 1
                if key_delay == 3:
                    text += key_to_type
                    key_delay = 0
                    keyboard.press(key_to_type)
            if hand1_fingers == FINGER_4 and len(text) > 1:
                text = text[:-1]
                keyboard.press(Key.backspace)
                sleep(0.15)
            cv2.rectangle(img, (OFFSET, 450), (830, 500), WHITE, cv2.FILLED)
            cv2.rectangle(img, (OFFSET, 450), (830, 500), BLUE, 1)
            cv2.putText(img, text[-40:], (OFFSET, 480), FONT, 1, BLACK, 2)
            cv2.circle(img, (idx_x, idx_y), 7, BLUE, cv2.FILLED)

            if hand1_fingers == FINGER_ALL:
                x0, y0, w, h = OFFSET, OFFSET, (RES_X - 200), (RES_Y - 200)
                cv2.rectangle(img, (x0, y0), (x0 + w, y0 + h), WHITE, cv2.FILLED)
                cv2.rectangle(img, (x0, y0), (x0 + w, y0 + h), BLUE, 1)
                for i, line in enumerate(INSTRUCTION.split('\n')):
                    cv2.putText(img, line, (x0 + 15, y0 + 15 + i * 15), FONT, 0.7, BLACK, 1)

        if all_hands[0]['side'] == 'Left':
            if hand1_fingers == FINGER_1 and not word_open:
                word_open = True
                os.startfile(r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE')
            if hand1_fingers == FINGER_1_2 and not excel_open:
                excel_open = True
                os.startfile(r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE')
            if hand1_fingers == FINGER_1_2_3 and not firefox_open:
                firefox_open = True
                os.startfile(r'C:\Program Files\Mozilla Firefox\firefox.exe')
            if hand1_fingers == FINGER_NONE and firefox_open:
                firefox_open = False
                os.system('TASKKILL /IM firefox.exe')
            if hand1_fingers == FINGER_1_4:
                break

    if len(all_hands) == 2:
        hand1_fingers = fingers_up(all_hands[0])
        hand2_fingers = fingers_up(all_hands[1])
        idx_x, idx_y, idx_z = all_hands[0]['coords'][8]

        # Set brush color
        if sum(hand2_fingers) == 1:
            brush_color = BLUE
        elif sum(hand2_fingers) == 2:
            brush_color = GREEN
        elif sum(hand2_fingers) == 3:
            brush_color = RED
        elif sum(hand2_fingers) == 4:
            brush_color = WHITE
        else:
            draw_board = np.ones((RES_Y, RES_X, 3), np.uint8) * 255

        # Set brush thickness
        if idx_z < -60:
            brush_thickness = 30
        elif idx_z <= -40:
            brush_thickness = 20
        else:
            brush_thickness = 10

        cv2.circle(img, (idx_x, idx_y), brush_thickness, brush_color, cv2.FILLED)

        if hand1_fingers == FINGER_1:
            if last_x == 0 and last_y == 0:
                last_x, last_y = idx_x, idx_y
            cv2.line(draw_board, (last_x, last_y), (idx_x, idx_y), brush_color, brush_thickness)
            last_x, last_y = idx_x, idx_y
        else:
            last_x, last_y = 0, 0

        img = cv2.addWeighted(img, 1, draw_board, 0.2, 0)

    cv2.imshow('Image', img)
    cv2.imshow('Board', draw_board)

    key = cv2.waitKey(1)
    if key == 27:
        break

with open('results/text.txt', 'w') as f:
    f.write(text)

cv2.imwrite('results/board.png', draw_board)