#!/usr/bin/env python
# -*- coding: latin-1 -*-


# dev_appserver.py app.yaml
# gcloud app deploy app.yaml --project ti4-card-images
"""
"""

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageColor

from google.appengine.api import memcache
from google.appengine.api import urlfetch

import hashlib
import io
import json
import logging
import math
import random
import re
import os
import os.path
import urllib
import webapp2

PARAGRAPH_LINE_HEIGHT_SCALE = 1.4

# -----------------------------------------------------------------------------

def getImage(name):
    dir = os.path.dirname(__file__)
    static = os.path.join(dir, 'static')
    file = os.path.join(static, name)
    return Image.open(file)

def getFont(name, size):
    dir = os.path.dirname(__file__)
    static = os.path.join(dir, 'static')
    file = os.path.join(static, name)
    return ImageFont.truetype(file, size)

def imageToJPEG(image):
    # BytesIO is bugged, write to a file.
    file = '/tmp/img' + str(random.random()) + '.jpg'
    f = open(file, 'wb')
    image.save(f, format='JPEG')
    f.close()
    f = open(file, 'rb')
    jpg = f.read()
    f.close()
    os.remove(file)
    return jpg

def nudgeY(font, text, maxX, y1, y2):
    (w, h) = font.getsize(text)
    return y1 if w <= maxX else y2

def getImageFromUrl(url):
    logging.info('getImageFromUrl: ' + url)
    hash = hashlib.sha1()
    hash.update(url.lower())
    key = hash.hexdigest().lower()
    result = urlfetch.fetch(url)
    file = '/tmp/image_' + key + '.jpg'
    f = open(file, 'wb')
    f.write(result.content)
    f.close()
    img = Image.open(file)
    os.remove(file)
    return img

# -----------------------------------------------------------------------------

_visualizeMargins = False

def wrapText(draw, font, text, x, y, maxX, fill, lineH):
    if _visualizeMargins:
        w = maxX
        h = 30
        color = (128, 128, 128, 64)
        draw.rectangle([(x, y), (x+w, y+h)], color)

    words = filter(None, text.split(' '))
    text = ''
    lineWidth = 0
    (spaceW, h) = font.getsize(' ')
    for word in words:
        (w, h) = font.getsize(word)
        if lineWidth > 0 and lineWidth + w > maxX:
            draw.text((x, y), text, font=font, fill=fill)
            text = ''
            lineWidth = 0
            y += lineH
        text += word + ' '
        lineWidth += w + spaceW
    draw.text((x, y), text, font=font, fill=fill)
    return y + (lineH * PARAGRAPH_LINE_HEIGHT_SCALE)

def wrapTextCenter(draw, font, text, x, y, maxX, fill, lineH):
    if _visualizeMargins:
        w = maxX / 2
        h = 30
        color = (128, 128, 128, 64)
        draw.rectangle([(x - w, y), (x + w, y+h)], color)

    words = filter(None, text.split(' '))
    text = ''
    lineWidth = 0
    (spaceW, h) = font.getsize(' ')
    for word in words:
        (w, h) = font.getsize(word)
        if lineWidth > 0 and lineWidth + w > maxX:
            x2 = x - (lineWidth / 2)
            draw.text((x2, y), text, font=font, fill=fill)
            text = ''
            lineWidth = 0
            y += lineH
        text += word + ' '
        lineWidth += w + spaceW
    x2 = x - (lineWidth / 2)
    draw.text((x2, y), text, font=font, fill=fill)
    return y + (lineH * PARAGRAPH_LINE_HEIGHT_SCALE)

def wrapTextCenterHV(draw, font, text, x, y, maxX, fill, lineH):
    if _visualizeMargins:
        w = maxX / 2
        h = 30
        color = (128, 128, 128, 64)
        draw.rectangle([(x - w, y), (x + w, y+h)], color)

    text = text.replace('\n', ' \n ')
    lines = []
    (spaceW, h) = font.getsize(' ')
    words = filter(None, text.split(' '))
    text = ''
    lineWidth = 0
    for word in words:
        (w, h) = font.getsize(word)
        if word == '\n' or (lineWidth > 0 and lineWidth + w > maxX):
            lines.append(text)
            text = ''
            lineWidth = 0
        if word == '\n':
            lines.append('')
        else:
            text += word + ' '
            lineWidth += w + spaceW
    lines.append(text)
    y = y - (len(lines) * lineH / 2)
    for line in lines:
        (lineWidth, h) = font.getsize(line)
        x2 = x - (lineWidth / 2)
        draw.text((x2, y), line, font=font, fill=fill)
        y += lineH
    return y + (lineH * PARAGRAPH_LINE_HEIGHT_SCALE)

def wrapTextCenterAlignBottom(draw, font, text, x, y, maxX, fill, lineH):
    if _visualizeMargins:
        w = maxX / 2
        h = 30
        color = (128, 128, 128, 64)
        draw.rectangle([(x - w, y), (x + w, y+h)], color)

    text = text.replace('\n', ' \n ')
    lines = []
    (spaceW, h) = font.getsize(' ')
    words = filter(None, text.split(' '))
    text = ''
    lineWidth = 0
    for word in words:
        (w, h) = font.getsize(word)
        if word == '\n' or (lineWidth > 0 and lineWidth + w > maxX):
            lines.append(text)
            text = ''
            lineWidth = 0
        if word == '\n':
            lines.append('')
        else:
            text += word + ' '
            lineWidth += w + spaceW
    lines.append(text)
    top = y - (len(lines) * lineH)
    y = top
    for line in lines:
        (lineWidth, h) = font.getsize(line)
        x2 = x - (lineWidth / 2)
        draw.text((x2, y), line, font=font, fill=fill)
        y += lineH
    return top

FONT_3_WORDS = {
    'SPACE',
    'CANNON',
    'BOMBARDMENT',
    'SUSTAIN',
    'DAMAGE',
    'ANTI-FIGHTER',
    'BARRAGE',
    'PLANETARY',
    'SHIELD',
    'PRODUCTION',

    # French
    unicode('DÉGÂTS', 'utf-8'),
    unicode('ENCAISSÉS', 'utf-8'),
    unicode('BARRAGE', 'utf-8'),
    unicode('ANTI-CHASSEUR', 'utf-8'),
    unicode('BOMBARDEMENT', 'utf-8'),
    unicode('BOUCLIER', 'utf-8'),
    unicode('PLANÉTAIRE', 'utf-8'),
    unicode('CANON', 'utf-8'),
    unicode('SPATIAL', 'utf-8'),
}

def wrapTextBoldStart(draw, font1, font2, font3, text, x, y, maxX, fill, lineH, dyfont3):
    if _visualizeMargins:
        w = maxX - x
        h = 30
        color = (128, 128, 128, 64)
        draw.rectangle([(x, y), (x+w, y+h)], color)

    font = font1
    (spaceW, h) = font.getsize(' ')
    words = filter(None, text.split(' '))
    text = ''
    startX = x
    indent = 0
    restoreFont = font1
    i = 0
    for word in words:
        isAction = (i == 0 and word.lower() == 'action:') or (i == 1 and word == ':' and words[i-1].lower() == 'action')
        isFor = word.lower() == 'for:' or (i > 0 and word == ':' and words[i-1].lower() == 'pour')
        isAgainst = word.lower() == 'against:' or (i > 0 and word == ':' and words[i-1].lower() == 'contre')

        dy = 0
        if font == font3:
            font = restoreFont
        if word in FONT_3_WORDS or re.sub(r'[^\w\s]', '', word) in FONT_3_WORDS:
            restoreFont = font
            font = font3
            dy = dyfont3
        if word.startswith('^'):
            word = word[1:]
            restoreFont = font
            font = font3
            dy = dyfont3
        (w, h) = font.getsize(word)
        if x + w > maxX:
            x = startX + indent
            y += lineH
        draw.text((x, y + dy), word, font=font, fill=fill)
        x += w + spaceW
        if (word.endswith(':') or word.endswith('.')) and font == font1:
            font = font2
            if (not isAction) and (not isFor) and (not isAgainst):
                x = startX
                y += lineH * PARAGRAPH_LINE_HEIGHT_SCALE
            if isFor or isAgainst:
                indent = 20
        i = i + 1
    return y + (lineH * PARAGRAPH_LINE_HEIGHT_SCALE)

# -----------------------------------------------------------------------------

CARD_W = 500
CARD_H = 750

ACTION_TITLE_L = 85
ACTION_TITLE_R = 105
ACTION_TITLE_Y1 = 96
ACTION_TITLE_Y2 = 76
ACTION_TITLE_TEXT_SIZE = 39
ACTION_TITLE_TEXT_H = 39

ACTION_BODY_L = 70
ACTION_BODY_R = 25
ACTION_BODY_Y = 206
ACTION_BODY_TEXT_SIZE = 31
ACTION_BODY_TEXT_H = 37
ACTION_BODY_UPPER_TEXT_SIZE = 24

ACTION_FLAVOR_L = 275
ACTION_FLAVOR_R = 100
ACTION_FLAVOR_LINE_DY = 15
ACTION_FLAVOR_Y = 730
ACTION_FLAVOR_TEXT_SIZE = 27
ACTION_FLAVOR_TEXT_H = 31

SECRET_TITLE_L = 250
SECRET_TITLE_R = 100
SECRET_TITLE_Y1 = 35
SECRET_TITLE_Y2 = 15
SECRET_TITLE_TEXT_SIZE = 44
SECRET_TITLE_TEXT_H = 44

SECRET_TYPE_L = 250
SECRET_TYPE_R = 100
SECRET_TYPE_Y = 128
SECRET_TYPE_TEXT_SIZE = 31
SECRET_TYPE_TEXT_H = 31

SECRET_BODY_L = 250
SECRET_BODY_R = 95
SECRET_BODY_Y = 395
SECRET_BODY_TEXT_SIZE = 38
SECRET_BODY_TEXT_H = 47

SECRET_FOOTER_L = 250
SECRET_FOOTER_R = 95
SECRET_FOOTER_Y = 707
SECRET_FOOTER_TEXT_SIZE = 30
SECRET_FOOTER_TEXT_H = 47

PUBLIC_TITLE_L = 250
PUBLIC_TITLE_R = 100
PUBLIC_TITLE_Y1 = 35
PUBLIC_TITLE_Y2 = 15
PUBLIC_TITLE_TEXT_SIZE = 43
PUBLIC_TITLE_TEXT_H = 43

PUBLIC_TYPE_L = 250
PUBLIC_TYPE_R = 100
PUBLIC_TYPE_Y = 128
PUBLIC_TYPE_TEXT_SIZE = 34
PUBLIC_TYPE_TEXT_H = 34

PUBLIC_BODY_L = 250
PUBLIC_BODY_R = 80
PUBLIC_BODY_Y = 395
PUBLIC_BODY_TEXT_SIZE = 39
PUBLIC_BODY_TEXT_H = 48

PUBLIC_FOOTER_L = 250
PUBLIC_FOOTER_R = 95
PUBLIC_FOOTER_Y = 705
PUBLIC_FOOTER_TEXT_SIZE = 32
PUBLIC_FOOTER_TEXT_H = 47

AGENDA_TITLE_L = 250
AGENDA_TITLE_R = 65
AGENDA_TITLE_Y1 = 55
AGENDA_TITLE_Y2 = 35
AGENDA_TITLE_TEXT_SIZE = 44
AGENDA_TITLE_TEXT_H = 44

AGENDA_TYPE_L = 250
AGENDA_TYPE_R = 100
AGENDA_TYPE_Y = 165
AGENDA_TYPE_TEXT_SIZE = 31
AGENDA_TYPE_TEXT_H = 31
AGENDA_BODY_UPPER_TEXT_SIZE = 24

AGENDA_BODY_ELECT_L = 250
AGENDA_BODY_ELECT_R = 105
AGENDA_BODY_FORAGAINST_L = 60
AGENDA_BODY_FORAGAINST_R = 105
AGENDA_BODY_Y = 225
AGENDA_BODY_TEXT_SIZE = 28
AGENDA_BODY_TEXT_H = 35

PROMISSORY_TITLE_L = 250
PROMISSORY_TITLE_R = 100 # 100
PROMISSORY_TITLE_Y1 = 55
PROMISSORY_TITLE_Y2 = 35
PROMISSORY_TITLE_TEXT_SIZE = 39
PROMISSORY_TITLE_TEXT_H = 39

PROMISSORY_BODY_L = 80
PROMISSORY_BODY_R = 80
PROMISSORY_BODY_Y = 180
PROMISSORY_BODY_TEXT_SIZE = 31
PROMISSORY_BODY_TEXT_H = 37
PROMISSORY_BODY_UPPER_TEXT_SIZE = 24

# REPLACE THESE WITH PER CARD CONSTANTS
TITLE_SIZE = 44
TITLE_LINEH = 44
TYPE_SIZE = 32
TYPE_LINEH = 32
BODY_SM_SIZE = 31
BODY_SM_LINEH = 37
BODY_LG_SIZE = 40
BODY_LG_LINEH = 47

def actionCard(title, body, flavor, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', ACTION_TITLE_TEXT_SIZE + titlesize)
    color = (255, 232, 150, 255)
    text = title
    x = ACTION_TITLE_L
    y1 = ACTION_TITLE_Y1
    y2 = ACTION_TITLE_Y2
    maxX = CARD_W - ACTION_TITLE_R
    lineH = ACTION_TITLE_TEXT_H + titlesize
    y = nudgeY(font, text, maxX, y1, y2)
    wrapText(draw, font, text, x, y, maxX, color, lineH)

    body = body.replace('Action:', 'ACTION:')
    body = body.replace('Action :', 'ACTION :')
    if ('ACTION:' in body) or ('ACTION :') in body:
        font1 = getFont('MyriadProBoldItalic.ttf', ACTION_BODY_TEXT_SIZE + fontsize)
    else:
        font1 = getFont('MyriadProBold.ttf', ACTION_BODY_TEXT_SIZE + fontsize)
    font2 = getFont('MyriadProSemibold.otf', ACTION_BODY_TEXT_SIZE + fontsize)
    font3 = getFont('HandelGothicDBold.otf', ACTION_BODY_UPPER_TEXT_SIZE + fontsize)

    color = (255, 255, 255, 255)
    text = body
    x = ACTION_BODY_L
    y = ACTION_BODY_Y
    maxX = CARD_W - ACTION_BODY_R
    lineH = ACTION_BODY_TEXT_H + fontsize
    for line in text.split('\n'):
        y = wrapTextBoldStart(draw, font1, font2, font3, line, x, y, maxX, color, lineH, 2)
        font1 = font2

    font = getFont('MyriadWebProItalic.ttf', ACTION_FLAVOR_TEXT_SIZE + fontsize)
    color = (255, 255, 255, 255)
    text = flavor
    x = ACTION_FLAVOR_L
    y = ACTION_FLAVOR_Y
    maxX = CARD_W - ACTION_FLAVOR_R
    lineH = ACTION_FLAVOR_TEXT_H + fontsize
    top = wrapTextCenterAlignBottom(draw, font, text, x, y, maxX, color, lineH)

    y = top - ACTION_FLAVOR_LINE_DY
    draw.line([(107, y), (CARD_W - 69, y)], fill=(255, 255, 255, 255), width=3)

    return imageToJPEG(img)

def secretObjectiveCard(title, type, body, footer, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', SECRET_TITLE_TEXT_SIZE + titlesize)
    color = (254, 196, 173, 255)
    text = title
    x = SECRET_TITLE_L
    y1 = SECRET_TITLE_Y1
    y2 = SECRET_TITLE_Y2
    maxX = CARD_W - SECRET_TITLE_R
    lineH = SECRET_TITLE_TEXT_H + titlesize
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    x = 125
    y = 130
    w = 250
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('HandelGothicDBold.otf', SECRET_TYPE_TEXT_SIZE)
    items = type.split('|')
    text = items[0]
    color = ImageColor.getrgb('#' + items[1])
    x = SECRET_TYPE_L
    y = SECRET_TYPE_Y
    maxX = CARD_W - SECRET_TYPE_R
    lineH = SECRET_TYPE_TEXT_H
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProSemibold.otf', SECRET_BODY_TEXT_SIZE + fontsize)
    color = (255, 255, 255, 255)
    text = body
    x = SECRET_BODY_L
    y = SECRET_BODY_Y
    maxX = CARD_W - SECRET_BODY_R
    lineH = SECRET_BODY_TEXT_H + fontsize
    y = wrapTextCenterHV(draw, font, text, x, y, maxX, color, lineH)

    x = 125
    y = 710
    w = 250
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('HandelGothicDBold.otf', SECRET_FOOTER_TEXT_SIZE)
    items = footer.split('|')
    text = items[0]
    color = ImageColor.getrgb('#' + items[1])
    x = SECRET_FOOTER_L
    y = SECRET_FOOTER_Y
    maxX = CARD_W - SECRET_FOOTER_R
    lineH = SECRET_FOOTER_TEXT_H
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    return imageToJPEG(img)

def publicObjectiveCard(level, title, type, body, footer, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', PUBLIC_TITLE_TEXT_SIZE + titlesize)
    color = (249, 249, 169, 255) if level == 1 else (173, 239, 254, 255)
    text = title
    x = PUBLIC_TITLE_L
    y1 = PUBLIC_TITLE_Y1
    y2 = PUBLIC_TITLE_Y2
    maxX = CARD_W - PUBLIC_TITLE_R
    lineH = PUBLIC_TITLE_TEXT_H + titlesize
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    x = 120
    y = 130
    w = 260
    h = 35
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('HandelGothicDBold.otf', PUBLIC_TYPE_TEXT_SIZE)
    items = type.split('|')
    text = items[0]
    color = ImageColor.getrgb('#' + items[1])
    x = PUBLIC_TYPE_L
    y = PUBLIC_TYPE_Y
    maxX = CARD_W - PUBLIC_TYPE_R
    lineH = PUBLIC_TYPE_TEXT_H
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProSemibold.otf', PUBLIC_BODY_TEXT_SIZE + fontsize)
    color = (255, 255, 255, 255)
    text = body
    x = PUBLIC_BODY_L
    y = PUBLIC_BODY_Y
    maxX = CARD_W - PUBLIC_BODY_R
    lineH = PUBLIC_BODY_TEXT_H + fontsize
    y = wrapTextCenterHV(draw, font, text, x, y, maxX, color, lineH)

    x = 110
    y = 710
    w = 280
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('HandelGothicDBold.otf', PUBLIC_FOOTER_TEXT_SIZE)
    items = footer.split('|')
    text = items[0]
    color = ImageColor.getrgb('#' + items[1])
    x = PUBLIC_FOOTER_L
    y = PUBLIC_FOOTER_Y
    maxX = CARD_W - PUBLIC_FOOTER_R
    lineH = PUBLIC_FOOTER_TEXT_H
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    return imageToJPEG(img)

def agendaCard(title, type, body, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', AGENDA_TITLE_TEXT_SIZE + titlesize)
    color = (149, 202, 255, 255)
    text = title
    x = AGENDA_TITLE_L
    y1 = AGENDA_TITLE_Y1
    y2 = AGENDA_TITLE_Y2
    maxX = CARD_W - AGENDA_TITLE_R
    lineH = AGENDA_TITLE_TEXT_H + titlesize
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    x = 200
    y = 160
    w = 100
    h = 30
    color = (24, 26, 25, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('MyriadProBold.ttf', AGENDA_TYPE_TEXT_SIZE)
    items = type.split('|')
    text = items[0]
    color = ImageColor.getrgb('#' + items[1])
    x = AGENDA_TYPE_L
    y = AGENDA_TYPE_Y
    maxX = CARD_W - AGENDA_TYPE_R
    lineH = AGENDA_TYPE_TEXT_H
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    #font1 = getFont('MyriadProBold.ttf', AGENDA_BODY_TEXT_SIZE)
    #font2 = getFont('MyriadProSemibold.otf', AGENDA_BODY_TEXT_SIZE)
    font2 = getFont('MyriadProRegular.ttf', AGENDA_BODY_TEXT_SIZE + fontsize)
    font3 = getFont('HandelGothicDBold.otf', AGENDA_BODY_UPPER_TEXT_SIZE + fontsize)
    color = (0, 0, 0, 255)
    text = body
    y = AGENDA_BODY_Y
    lineH = AGENDA_BODY_TEXT_H + fontsize

    if '(When' in text:
        i = text.find('(When')
        j = text.find(')', i + 1)
        whenText = text[i+1:j]
        if text[j+1] == '\n':
            j += 1
        text = text[:i] + text[j+1:]
        y = wrapTextCenter(draw, font2, whenText, x, y, maxX, color, lineH)

    if 'Elect ' in text or 'Élisez ' in text:
        font1 = getFont('MyriadProSemibold.otf', AGENDA_BODY_TEXT_SIZE + fontsize)
        x = AGENDA_BODY_ELECT_L
        maxX = CARD_W - AGENDA_BODY_ELECT_R
        for line in text.split('\n'):
            if line.startswith('Elect ') or lines.startswith('Élisez '):
                y = wrapTextCenter(draw, font1, line, x, y, maxX, color, lineH)
            else:
                y = wrapTextCenter(draw, font2, line, x, y, maxX, color, lineH)
    else:
        font1 = getFont('MyriadProSemiboldItalic.ttf', AGENDA_BODY_TEXT_SIZE + fontsize)
        x = AGENDA_BODY_FORAGAINST_L
        maxX = CARD_W - AGENDA_BODY_FORAGAINST_R
        for line in text.split('\n'):
            isFor = line.startswith('For:') or line.startswith('Pour :')
            isAgainst = line.startswith('Against:') or line.startswith('Contre :')
            if isFor or isAgainst:
                y = wrapTextBoldStart(draw, font1, font2, font3, line, x, y, maxX, color, lineH, 1)
            else:
                y = wrapText(draw, font2, line, x, y, maxX, color, lineH)

    return imageToJPEG(img)

def promissoryCard(color, title, body, titlesize, fontsize):
    filename = 'Promissory_' + color + '.jpg'
    img = getImage(filename)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', PROMISSORY_TITLE_TEXT_SIZE + titlesize)
    color = (255, 255, 255, 255)
    text = title
    x = PROMISSORY_TITLE_L
    y1 = PROMISSORY_TITLE_Y1
    y2 = PROMISSORY_TITLE_Y2
    maxX = CARD_W - PROMISSORY_TITLE_R
    lineH = PROMISSORY_TITLE_TEXT_H + titlesize
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font1 = getFont('MyriadProBold.ttf', PROMISSORY_BODY_TEXT_SIZE + fontsize)
    font2 = getFont('MyriadProSemibold.otf', PROMISSORY_BODY_TEXT_SIZE + fontsize)
    font3 = getFont('HandelGothicDBold.otf', PROMISSORY_BODY_UPPER_TEXT_SIZE + fontsize)

    color = (0, 0, 0, 255)
    text = body
    x = PROMISSORY_BODY_L
    y = PROMISSORY_BODY_Y
    maxX = CARD_W - PROMISSORY_BODY_R
    lineH = PROMISSORY_BODY_TEXT_H + fontsize
    for line in text.split('\n'):
        y = wrapTextBoldStart(draw, font1, font2, font3, line, x, y, maxX, color, lineH, 2)
        font1 = font2

    return imageToJPEG(img)

def nobilityCard(color, title, type, body, footer, points, titlesize, fontsize):
    filename = 'Nobility' + color + '.jpg'
    img = getImage(filename)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', TITLE_SIZE + titlesize)
    color = (255, 255, 255, 255)
    text = title
    x = 250
    y1 = 35
    y2 = 15
    maxX = 400
    lineH = TITLE_LINEH + titlesize
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProBold.ttf', TYPE_SIZE)
    items = type.split('|')
    text = items[0]
    color = ImageColor.getrgb('#' + items[1])
    x = 250
    y = 135
    maxX = 400
    lineH = TYPE_LINEH
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProSemibold.otf', BODY_LG_SIZE + fontsize)
    color = (255, 255, 255, 255)
    text = body
    x = 250
    y = 375
    maxX = 450
    lineH = BODY_LG_LINEH + fontsize
    y = wrapTextCenterHV(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProBold.ttf', 40)
    color = (255, 255, 255, 255) if footer.lower() == 'public' else (255, 0, 0, 255)
    text = footer
    x = 250
    y = 520
    maxX = 450
    lineH = 40
    y = wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('HandelGothicDBold.otf', 130)
    color = (255, 255, 255, 255)
    text = str(points)
    x = 265
    y = 565
    maxX = 450
    lineH = 130
    y = wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    return imageToJPEG(img)

# -----------------------------------------------------------------------------

CARD_OPTIONS = {
    'action' : {
        'cardType' : 'action',
        'cardImage' : 'ActionCard.jpg',
        'back' : 'Action_Back.jpg',
    },
    'action-c' : {
        'cardType' : 'action',
        'cardImage' : 'ActionCard_c.jpg',
        'back' : 'Action_Back.jpg',
    },
    'action_codex' : {
        'cardType' : 'action',
        'cardImage' : 'ActionCardCodex.jpg',
        'back' : 'Action_Back.jpg',
    },
    'secret' : {
        'cardType' : 'secret',
        'cardImage' : 'SecretObjective.jpg',
        'back' : 'SecretObjective_Back.jpg',
    },
    'secret-c' : {
        'cardType' : 'secret',
        'cardImage' : 'SecretObjective_c.jpg',
        'back' : 'SecretObjective_Back.jpg',
    },
    'stage1' : {
        'cardType' : 'public1',
        'cardImage' : 'Stage1.jpg',
        'back' : 'Stage1_Back.jpg',
    },
    'stage1-c' : {
        'cardType' : 'public1',
        'cardImage' : 'Stage1_c.jpg',
        'back' : 'Stage1_Back.jpg',
    },
    'stage2' : {
        'cardType' : 'public2',
        'cardImage' : 'Stage2.jpg',
        'back' : 'Stage2_Back.jpg',
    },
    'stage2-c' : {
        'cardType' : 'public2',
        'cardImage' : 'Stage2_c.jpg',
        'back' : 'Stage2_Back.jpg',
    },
    'agenda' : {
        'cardType' : 'agenda',
        'cardImage' : 'Agenda.jpg',
        'back' : 'Agenda_Back.jpg',
    },
    'agenda-c' : {
        'cardType' : 'agenda',
        'cardImage' : 'Agenda_c.jpg',
        'back' : 'Agenda_Back.jpg',
    },
    'promissory-c' : {
        'cardType' : 'promissory',
        'cardImage' : False
    },
    'nobility' : {
        'cardType' : 'nobility',
        'cardImage' : False
    }
}

class CardHandler(webapp2.RequestHandler):
    def get(self):
        card = self.request.get('card', 'action').lower()
        title = self.request.get('title', 'title').upper()
        type = self.request.get('type', 'type').upper()
        body = self.request.get('body', 'body')
        flavor = self.request.get('flavor', 'flavor')
        footer = self.request.get('footer', 'footer').upper()
        color = self.request.get('color', 'white').capitalize()
        points = self.request.get('points', '1').lower()
        titlesize = self.request.get('titlesize', '0').lower()
        fontsize = self.request.get('fontsize', '0').lower()

        logging.info('Card "' + card + '" title="' + title + '" type="' + type + '" body="' + body + '" flavor="' + flavor + '"')

        hash = hashlib.sha256()
        hash.update(card.encode('utf-8'))
        hash.update(title.encode('utf-8'))
        hash.update(type.encode('utf-8'))
        hash.update(body.encode('utf-8'))
        hash.update(footer.encode('utf-8'))
        hash.update(flavor.encode('utf-8'))
        hash.update(color.encode('utf-8'))
        hash.update(points.encode('utf-8'))
        hash.update(titlesize.encode('utf-8'))
        hash.update(fontsize.encode('utf-8'))
        hash.update('version8')
        key = hash.hexdigest().lower()

        cardOptions = CARD_OPTIONS[card]
        cardType = cardOptions['cardType']
        cardImage = cardOptions['cardImage']
        titlesize = int(titlesize)
        fontsize = int(fontsize)

        jpg = memcache.get(key=key)
        #jpg = None
        if jpg is None:
            if cardType == 'action':
                jpg = actionCard(title, body, flavor, cardImage, titlesize, fontsize)
            elif cardType == 'secret':
                jpg = secretObjectiveCard(title, type, body, footer, cardImage, titlesize, fontsize)
            elif cardType == 'public1':
                jpg = publicObjectiveCard(1, title, type, body, footer, cardImage, titlesize, fontsize)
            elif cardType == 'public2':
                jpg = publicObjectiveCard(2, title, type, body, footer, cardImage, titlesize, fontsize)
            elif cardType == 'agenda':
                jpg = agendaCard(title, type, body, cardImage, titlesize, fontsize)
            elif cardType == 'promissory':
                jpg = promissoryCard(color, title, body, titlesize, fontsize)
            elif cardType == 'nobility':
                jpg = nobilityCard(color, title, type, body, footer, points, titlesize, fontsize)
            else:
                self.response.status = 400 # bad request
                self.response.status_message = 'Bad card type'
                self.response.out.write('Bad card type "' + card + '"')
                return
            memcache.add(key, jpg, 3600)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class BackHandler(webapp2.RequestHandler):
    def get(self):
        card = self.request.get('card', 'action').lower()
        cardOptions = CARD_OPTIONS[card]
        backImage = cardOptions['back']
        key = backImage
        jpg = memcache.get(key=key)
        #jpg = None
        if jpg is None:
            img = getImage(backImage)
            jpg = imageToJPEG(img)
            memcache.add(key, jpg, 3600)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class getActionHandler(webapp2.RequestHandler):
    def get(self):
        title = self.request.get('title').upper()
        body = self.request.get('body')
        flavor = self.request.get('flavor')
        source = self.request.get('source')
        cardImage = 'ActionCardCodex.jpg' if source == 'codex' else 'ActionCard_c.jpg'
        titlesize = 0
        fontsize = 0
        jpg = actionCard(title, body, flavor, cardImage, titlesize, fontsize)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class getAgendaHandler(webapp2.RequestHandler):
    def get(self):
        title = self.request.get('title').upper()
        type = self.request.get('type').upper()
        elect = self.request.get('elect')
        forText = self.request.get('for')
        againstText = self.request.get('against')
        source = self.request.get('source')
        cardImage = 'Agenda_c.jpg'
        titlesize = 0
        fontsize = 0

        if type == 'DIRECTIVE':
            type = 'DIRECTIVE|ffff00'
        elif type == 'LAW':
            type = 'LAW|ddad63'

        body = ''
        if len(elect) > 1:
            body += 'Elect '
            body += elect + '\n'
            if len(againstText) > 1:
                body += 'For: ' + forText + '\nAgainst: ' + againstText
            else:
                body += forText
        else:
            if len(againstText) > 1:
                body += 'For: ' + forText + '\nAgainst: ' + againstText
            else:
                body += forText

        jpg = agendaCard(title, type, body, cardImage, titlesize, fontsize)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)


class TestActionHandler(webapp2.RequestHandler):
    def get(self):
        title = 'Bribery'
        body = 'After the speaker votes on an agenda: Spend any number of trade goods. For each trade good spent, cast 1 additional vote for any outcome.'
        flavor = u'\u201CWe think that this initiative would spell disaster for the galaxy, not just the Creuss.\u201D Taivra said, quietly slipping Z\u2018eu an envelope. \u201CDon\u2019t you agree?\u201D'
        jpg = actionCard(title.upper(), body, flavor, 2)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class TestSecretHandler(webapp2.RequestHandler):
    def get(self):
        title = 'Become the Gatekeeper'
        type = 'Status Phase'
        body = 'Have 1 or more ships in a system that contains an alpha wormhole and 1 or more ships in a system that contains a beta wormhole.'
        jpg = secretObjectiveCard(title.upper(), type.upper(), body)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class TestPublicHandler(webapp2.RequestHandler):
    def get(self):
        stage = 1
        title = 'Lead From the Front'
        body = 'Spend a total of 3 tokens from your tactic and/or strategy pools.'
        jpg = publicObjectiveCard(stage, title.upper(), body)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class TestAgenda1Handler(webapp2.RequestHandler):
    def get(self):
        title = 'Research Team: Propulsion'
        type = 'law'
        body = u'Elect Industrial Planet\nAttach this card to the elected planet\u2019s card.\nWhen the owner of this planet researches technology, he may exhaust this card to ignore 1 blue prerequisite.'
        jpg = agendaCard(title.upper(), type.upper(), body)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class TestAgenda2Handler(webapp2.RequestHandler):
    def get(self):
        title = 'Economic Equality'
        type = 'directive'
        body = 'For: Each player returns all of his trade goods to the supply. Then, each player gains 5 trade goods.\nAgainst: Each player returns all of his trade goods to the supply.'
        jpg = agendaCard(title.upper(), type.upper(), body)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

# Given a 3200x3200 system tile image, generate a 2048x1024 one.
class MutateSystemTile(webapp2.RequestHandler):
    def get(self):
        original = getImageFromUrl(self.request.get('image'))
        front = original.crop((1390, 1630, 3170, 3170))
        front = front.resize((1014 - 9, 947 - 76))
        back = original.crop((1382, 30, 3170, 1570))
        back = back.resize((2038 - 1033, 947 - 76))
        img = Image.new('RGB', (2048, 1024), 'black')
        img.paste(front, (9, 76, 1014, 947))
        img.paste(back, (1033, 76, 2038, 947))
        jpg = imageToJPEG(img)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

# Convert command and owner tokens to the new 512x512 shared image.
class MutateFactionTokens(webapp2.RequestHandler):
    def get(self):
        command = getImageFromUrl(self.request.get('command'))
        owner = getImageFromUrl(self.request.get('owner'))
        img = Image.new('RGB', (512, 512), 'black')
        #command = getImage('commandToken.png')
        #owner = getImage('ownerToken.png')
        #img = getImage('playertokens_uv.png')

        commandTop = command.crop((450, 0, 900, 450))
        commandTop = commandTop.rotate(270)
        x = 141
        y = 311
        dx = 175
        dy = 175
        commandTop = commandTop.resize((dx * 2, dy * 2))
        mask = Image.new('RGBA', (dx * 2, dy * 2))
        draw = ImageDraw.Draw(mask)
        draw.polygon([(0, 350), (195, 50), (370, 350)], (255, 255, 255, 255))
        img.paste(commandTop, (x-dx, y-dy, x+dx, y+dy), mask)

        commandBottom = command.crop((450, 450, 900, 900))
        commandBottom = commandBottom.rotate(90)
        x = 336
        y = 351
        dx = 150
        dy = 150
        commandBottom = commandBottom.resize((dx * 2, dy * 2))
        mask = Image.new('RGBA', (dx * 2, dy * 2))
        draw = ImageDraw.Draw(mask)
        draw.polygon([(10, 0), (165, 280), (320, 0)], (255, 255, 255, 255))
        img.paste(commandBottom, (x-dx, y-dy, x+dx, y+dy), mask)

        owner = owner.rotate(270)
        owner = owner.crop((0, 190, 340, 400))
        x = 256
        y = 96
        dx = 124
        dy = 77
        owner = owner.resize((dx * 2, dy * 2))
        img.paste(owner, (x-dx, y-dy, x+dx, y+dy))

        border = getImage('playertokens_border.png')
        img.paste(border, (0, 0, 512, 512), border)

        #img = Image.blend(img, getImage('playertokens_uv.png'), 0.2)

        img = img.convert('RGB')

        jpg = imageToJPEG(img)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class RadialDither(webapp2.RequestHandler):
    def get(self):
        center = ImageColor.getrgb('#' + self.request.get('center', 'ffffff'))
        edge = ImageColor.getrgb('#' + self.request.get('edge', '000000'))
        size = int(self.request.get('size', 128))
        bits = int(self.request.get('bits', 5))
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        dr = edge[0] - center[0]
        dg = edge[1] - center[1]
        db = edge[2] - center[2]
        quant = 2 ^ bits
        for x in range(0, size):
            for y in range(0, size):
                dx = x - (size / 2)
                dy = y - (size / 2)

                # Actual U
                u = math.sqrt((dx * dx) + (dy * dy)) / (size / 2)

                # Quantized U
                uq = math.floor(u * quant) / quant

                # U2 is 0:1 how far along the quant.
                u2 = (u - uq) * quant

                # Replace U with either pre or post quant.
                u = uq
                if random.random() < u2:
                    u = u + 1.0 / quant

                # Noise step, keep or push to neighbor.
                r = random.random()
                if r < 0.1:
                    u = u - 3.0 / quant
                elif r < 0.2:
                    u = u - 2.0 / quant
                elif r < 0.3:
                    u = u - 1.0 / quant
                elif r > 0.9:
                    u = u + 3.0 / quant
                elif r > 0.8:
                    u = u + 2.0 / quant
                elif r > 0.7:
                    u = u + 1.0 / quant
                u = min(u, 1)
                u = max(u, 0)

                r = int(center[0] + (dr * u))
                g = int(center[1] + (dg * u))
                b = int(center[2] + (db * u))
                pixels[x,y] = (r, g, b)
        jpg = imageToJPEG(img)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class FourK(webapp2.RequestHandler):
    def get(self):
        img = getImageFromUrl(self.request.get('img'))
        img = img.convert('RGB')
        w, h = img.size
        w0, h0 = w, h
        if w > 4096:
            h = int(h * 4096 / w)
            w = 4096
        if h > 4096:
            w = int(w * 4096 / h)
            h = 4096
        logging.info('4k resizing from ' + str(w0) + 'x' + str(h0) + ' -> ' + str(w) + 'x' + str(h))
        img = img.resize((w, h))
        jpg = imageToJPEG(img)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class CardSheet(webapp2.RequestHandler):
    def post(self):
        cardw = int(self.request.get('cardw', 500))
        cardh = int(self.request.get('cardh', 750))
        cols = int(self.request.get('cols', 0))
        file = self.request.get('file', False)
        back = self.request.get('back', False)
        body = urllib.unquote(self.request.body)
        while body.endswith('='):
            body = body[:-1]
        logging.info('body: ' + body)
        #if len(body) == 0:
        #    body = '[{ "name": "A", "img": "url" }]'
        items = json.loads(body)
        logging.info('body: ' + body + ' #=' + str(len(items)))
        if cols == 0:
            cols = int(math.floor(4096 / cardw))
        rows = int(math.ceil(float(len(items)) / cols))
        rows = max(rows, 2) # must have at least 2 rows
        logging.info('cardSheet: ' + str(cols) + 'x' + str(rows))
        img = Image.new('RGB', (cardw * cols, cardh * rows))
        back = Image.open(back)
        for col in range(cols):
            for row in range(rows):
                x = cardw * col
                y = cardh * row
                i = (row * cols) + col
                card = False
                if i < len(items):
                    item = items[i]
                    logging.info(str(i) + ' "' + item['name'] + '" ' + item['img'])
                    card = getImageFromUrl(item['img'])
                else:
                    card = back
                card = card.resize((cardw, cardh))
                img.paste(card, (x, y, x+cardw, y+cardh))
        f = open(file, 'wb')
        img.save(f, format='JPEG')
        f.close()

class Proxy(webapp2.RequestHandler):
    def get(self):
        file = self.request.get('file', '/tmp/t.jpg')
        img = Image.open(file)
        jpg = imageToJPEG(img)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

app = webapp2.WSGIApplication([
    ('/img', CardHandler),
    ('/back', BackHandler),
    ('/getaction', getActionHandler),
    ('/getagenda', getAgendaHandler),
    #('/testaction', TestActionHandler),
    #('/testsecret', TestSecretHandler),
    #('/testpublic', TestPublicHandler),
    #('/testagenda', TestAgenda1Handler),
    #('/testagenda2', TestAgenda2Handler),
    ('/mutatesystem', MutateSystemTile),
    #('/mutatefaction', MutateFactionTokens),
    #('/radialdither', RadialDither),
    #('/4k', FourK),
    ('/cardsheet', CardSheet),
    ('/proxy', Proxy),

], debug=True)
