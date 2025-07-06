import cv2
import mediapipe as mp
import os
import numpy as np
from time import sleep
from pynput.keyboard import Controller, Key

COR_BRANCO = (255, 255, 255)
COR_PRETO = (0, 0, 0)
COR_AZUL = (255, 0, 0)
COR_VERDE = (0, 255, 0)
COR_VERMELHO = (0, 0, 255)
COR_AZUL_CLARO = (255, 255, 0)

mp_maos = mp.solutions.hands
mp_desenho = mp.solutions.drawing_utils
maos = mp_maos.Hands()

camera = cv2.VideoCapture(0)
resolucao_x = 1280
resolucao_y = 720
camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolucao_x)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolucao_y)
font_style = cv2.FONT_HERSHEY_DUPLEX
word_app = False
firefox_app = False
excel_app = False
dedos_true_1 = [False, True, False, False, False]
dedos_true_1_2 = [False, True, True, False, False]
dedos_true_1_2_3 = [False, True, True, True, False]
dedos_true_1_4 = [False, True, False, False, True]
dedos_true_4 = [False, False, False, False, True]
dedos_false = [False, False, False, False, False]
teclas = [['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'O', 'P'],
          ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'K', 'L'],
          ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'M', ',', '.', ';']]
offset = 50
tamanho = 50
contador = 0
texto = ">"
teclado = Controller()
img_quadro = np.ones((resolucao_y, resolucao_x, 3), np.uint8) * 255
cor_pincel = COR_AZUL
espessura_pincel = 1
x_quadro, y_quadro = 0, 0

# Texto de instruções
instrucao_texto = (
    """
    *Escrever texto*:\n
        Use a mao direita. Toque nas teclas virtuais com o indicador para digitar.\n
        Para apagar, levante apenas o dedo mindinho da mão direita.\n
        *Abrir aplicativos* (mão esquerda):\n
            - Indicador levantado: abre o Word\n
            - Indicador e médio levantados: abre o Excel\n
            - Indicador, médio e anelar levantados: abre o Firefox\n
            - Todos os dedos fechados: fecha o Firefox\n
    *Desenhar* (duas mãos):\n
        Mão esquerda define a cor do pincel:\n
            - 1 dedo levantado: azul\n
            - 2 dedos levantados: verde\n
            - 3 dedos levantados: vermelho\n
            - 4 dedos levantados: borracha\n
            - Todos os dedos fechados: limpa o quadro\n
        Mão direita desenha na tela com o indicador.\n
        A distância da mão direita até a câmera altera a espessura do pincel.
    """
)

def encotra_coordenadas_maos(img, lado_invertido = False):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resultado = maos.process(img_rgb)
    todas_maos = []
    if resultado.multi_hand_landmarks:
        for lado_mao, marcacoes_maos in zip(resultado.multi_handedness, resultado.multi_hand_landmarks):
            info_mao = {}
            coordenadas = []
            for marcacao in marcacoes_maos.landmark:
                coord_x, coord_y, coord_z = int(marcacao.x * resolucao_x), int(marcacao.y * resolucao_y), int(marcacao.z * resolucao_x)
                coordenadas.append((coord_x, coord_y, coord_z))   
            info_mao['coordenadas'] = coordenadas
            if lado_invertido:
                if lado_mao.classification[0].label == 'Left':
                    info_mao['lado'] = 'Right'
                else:
                    info_mao['lado'] = 'Left'
            else:
                info_mao['lado'] = lado_mao.classification[0].label
                        
            todas_maos.append(info_mao)
            mp_desenho.draw_landmarks(img,
                                    marcacoes_maos, 
                                    mp_maos.HAND_CONNECTIONS)
    return img, todas_maos

def dedos_levantados(mao):
    dedos = []
    if mao['lado'] == 'Right': 
        if mao['coordenadas'][4][0] < mao['coordenadas'][3][0]:
            dedos.append(True)
        else:
            dedos.append(False)
    else:
        if mao['coordenadas'][4][0] > mao['coordenadas'][3][0]:
            dedos.append(True)
        else:
            dedos.append(False)
    for ponta_dedo in [8,12,16,20]:
        if mao['coordenadas'][ponta_dedo][1] < mao['coordenadas'][ponta_dedo - 2][1]:
            dedos.append(True)
        else:
            dedos.append(False)
    return dedos

def imprime_botoes(img, posicao, letra, tamanho = 50, cor_retangulo = COR_BRANCO):
    cv2.rectangle(img, posicao, (posicao[0] + tamanho, posicao[1] + tamanho), cor_retangulo, cv2.FILLED)
    cv2.rectangle(img, posicao, (posicao[0] + tamanho, posicao[1] + tamanho), COR_AZUL, 1)
    cv2.putText(img, letra, (posicao[0] + 15, posicao[1] + 30), font_style, 1, COR_PRETO, 2)
    return img

while True:
    sucesso, img = camera.read()
    img = cv2.flip(img, 1)
    img, todas_maos = encotra_coordenadas_maos(img)

    # Retângulo fixo com dica de instrução
    dica_texto = "Veja as instrucoes ao levantar dois polegares e saia da aplicacao com 'ESC'."
    x_dica, y_dica, w_dica, h_dica = 0, 0, resolucao_x, 50
    cv2.rectangle(img, (x_dica, y_dica), (x_dica + w_dica, y_dica + h_dica), COR_BRANCO, cv2.FILLED)
    cv2.rectangle(img, (x_dica, y_dica), (x_dica + w_dica, y_dica + h_dica), COR_AZUL, 1)
    cv2.putText(img, dica_texto, (x_dica + 15, y_dica + 35), font_style, 0.5, COR_PRETO, 1)

    if len(todas_maos) == 1:
        info_dedos_mao1 = dedos_levantados(todas_maos[0])
        if todas_maos[0]['lado'] == 'Right':
            indicador_x, indicador_y, indicador_z = todas_maos[0]['coordenadas'][8]
            cv2.putText(img, f"Distancia camera: {indicador_z}", (850, 50), font_style, 1, COR_PRETO, 2)
            for indice_linha, linha_teclado in enumerate(teclas):
                for indice, letra in enumerate(linha_teclado):
                    if sum(info_dedos_mao1) <= 1:
                        letra = letra.lower()
                    img = imprime_botoes(img, (offset + indice * (tamanho + 30), offset + indice_linha * (tamanho + 30)), letra)
                    if (offset + indice * 80) < indicador_x < (100 + indice * 80) and (offset + indice_linha * 80) < indicador_y < (100 + indice_linha * 80):
                        img = imprime_botoes(img, (offset + indice * (tamanho + 30), offset + indice_linha * (tamanho + 30)), letra, cor_retangulo = COR_VERDE)
                        if indicador_z < -65:
                            contador = 1
                            escreve = letra
                            img = imprime_botoes(img, (offset + indice * (tamanho + 30), offset + indice_linha * (tamanho + 30)), letra, cor_retangulo = COR_AZUL_CLARO)
            if contador:
                contador += 1
                if contador == 3:
                    texto += escreve
                    contador = 0
                    teclado.press(escreve)
            if info_dedos_mao1 == dedos_true_4 and len(texto) > 1:
                texto = texto[:-1]
                teclado.press(Key.backspace)
                sleep(0.15)
            cv2.rectangle(img, (offset, 450), (830, 500), COR_BRANCO, cv2.FILLED)
            cv2.rectangle(img, (offset, 450), (830, 500), COR_AZUL, 1)
            cv2.putText(img, texto[-40:], (offset, 480), font_style, 1, COR_PRETO, 2)
            cv2.circle(img, (indicador_x, indicador_y), 7, COR_AZUL, cv2.FILLED)

        if todas_maos[0]['lado'] == 'Left':
            if info_dedos_mao1 == dedos_true_1 and word_app == False:
                word_app = True
                os.startfile(r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE')
            if info_dedos_mao1 == dedos_true_1_2 and excel_app == False:
                excel_app = True
                os.startfile(r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE')
            if info_dedos_mao1 == dedos_true_1_2_3 and firefox_app == False:
                firefox_app = True
                os.startfile(r'C:\Program Files\Mozilla Firefox\firefox.exe')
            if info_dedos_mao1 == dedos_false and firefox_app == True:
                firefox_app = False
                os.system('TASKKILL /IM firefox.exe')
            if info_dedos_mao1 == dedos_true_1_4:
                break

    if len(todas_maos) == 2:
        info_dedos_mao1 = dedos_levantados(todas_maos[0])
        info_dedos_mao2 = dedos_levantados(todas_maos[1])

        indicador_x, indicador_y, indicador_z = todas_maos[0]['coordenadas'][8]

        if sum(info_dedos_mao2) == 1:
            cor_pincel = COR_AZUL
        elif sum(info_dedos_mao2) == 2:
            cor_pincel = COR_VERDE
        elif sum(info_dedos_mao2) == 3:
            cor_pincel = COR_VERMELHO
        elif sum(info_dedos_mao2) == 4:
            cor_pincel = COR_BRANCO
        else:
            img_quadro = np.ones((resolucao_y, resolucao_x, 3), np.uint8) * 255
        
        # espessura_pincel = int(abs(indicador_z)) // 3 + 5
        if indicador_z < -60:
            espessura_pincel = 30
        elif indicador_z <= -40:
            espessura_pincel = 20
        else:
            espessura_pincel = 10
            
        cv2.circle(img, (indicador_x, indicador_y), espessura_pincel, cor_pincel, cv2.FILLED)

        if info_dedos_mao1 == dedos_true_1:
            if x_quadro == 0 and y_quadro ==0:
                x_quadro, y_quadro = indicador_x, indicador_y
            cv2.line(img_quadro, (x_quadro, y_quadro), (indicador_x, indicador_y), cor_pincel, espessura_pincel)
            x_quadro, y_quadro = indicador_x, indicador_y
            
        else:
            x_quadro, y_quadro = 0, 0
        
        img = cv2.addWeighted(img, 1, img_quadro, 0.2, 0)

    # Exibir instruções se os dois polegares estiverem levantados (e nenhum outro dedo) - melhorar essa chamada!
    if len(todas_maos) == 2:
        dedos_mao1 = dedos_levantados(todas_maos[0])
        dedos_mao2 = dedos_levantados(todas_maos[1])
        if dedos_mao1[0] and dedos_mao2[0] and not any(dedos_mao1[1:]) and not any(dedos_mao2[1:]):
            # Caixa de instruções
            x0, y0, w, h = 50, 50, (resolucao_x - 50), (resolucao_y - 50)
            cv2.rectangle(img, (x0, y0), (x0 + w, y0 + h), COR_BRANCO, cv2.FILLED)
            cv2.rectangle(img, (x0, y0), (x0 + w, y0 + h), COR_AZUL, 2)
            for i, linha in enumerate(instrucao_texto.split('\n')):
                cv2.putText(img, linha, (x0 + 20, y0 + 40 + i * 35), font_style, 0.5, COR_PRETO, 1)

    cv2.imshow('Imagem', img)
    cv2.imshow('Quadro', img_quadro)

    tecla = cv2.waitKey(1)
    if tecla == 27:
        break

with open('/results/text.txt', 'w') as arquivo:
    arquivo.write(texto)

cv2.imwrite('/results/quadro.png', img_quadro)