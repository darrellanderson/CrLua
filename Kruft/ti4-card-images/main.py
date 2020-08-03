#!/usr/bin/env python
# -*- coding: latin-1 -*-


# dev_appserver.py app.yaml
# gcloud app deploy app.yaml --project ti4-card-images
"""
"""

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from google.appengine.api import memcache

import hashlib
import io
import logging
import os
import os.path
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
    file = '/tmp/card.jpg'
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

# -----------------------------------------------------------------------------

def wrapText(draw, font, text, x, y, maxX, fill, lineH):
    words = filter(None, text.split(' '))
    text = ''
    lineWidth = 0
    (spaceW, h) = font.getsize(' ')
    for word in words:
        (w, h) = font.getsize(word)
        if lineWidth + w > maxX:
            draw.text((x, y), text, font=font, fill=fill)
            text = ''
            lineWidth = 0
            y += lineH
        text += word + ' '
        lineWidth += w + spaceW
    draw.text((x, y), text, font=font, fill=fill)
    return y + (lineH * PARAGRAPH_LINE_HEIGHT_SCALE)

def wrapTextCenter(draw, font, text, x, y, maxX, fill, lineH):
    words = filter(None, text.split(' '))
    text = ''
    lineWidth = 0
    (spaceW, h) = font.getsize(' ')
    for word in words:
        (w, h) = font.getsize(word)
        if lineWidth + w > maxX:
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
    text = text.replace('\n', ' \n ')
    lines = []
    (spaceW, h) = font.getsize(' ')
    words = filter(None, text.split(' '))
    text = ''
    lineWidth = 0
    for word in words:
        (w, h) = font.getsize(word)
        if word == '\n' or lineWidth + w > maxX:
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

def wrapTextBoldStart(draw, font1, font2, text, x, y, maxX, fill, lineH):
    font = font1
    (spaceW, h) = font.getsize(' ')
    words = filter(None, text.split(' '))
    text = ''
    startX = x
    indent = 0
    for word in words:
        (w, h) = font.getsize(word)
        if x + w > maxX:
            x = startX + indent
            y += lineH
        draw.text((x, y), word, font=font, fill=fill)
        x += w + spaceW
        if (word.endswith(':') or word.endswith('.')) and font == font1:
            font = font2
            (spaceW, spaceH) = font.getsize(' ')
            if word.lower() != 'action:' and word.lower() != 'for:' and word.lower() != 'against:':
                x = startX
                y += lineH * PARAGRAPH_LINE_HEIGHT_SCALE
            if word.lower() == 'for:' or word.lower() == 'against:':
                indent = 20
    return y + (lineH * PARAGRAPH_LINE_HEIGHT_SCALE)

# -----------------------------------------------------------------------------

CARD_W = 500
CARD_H = 750

ACTION_TITLE_L = 85
ACTION_TITLE_R = 100
ACTION_TITLE_Y1 = 96
ACTION_TITLE_Y2 = 76
ACTION_TITLE_TEXT_SIZE = 39
ACTION_TITLE_TEXT_H = 39

ACTION_BODY_L = 70
ACTION_BODY_R = 40
ACTION_BODY_Y = 206
ACTION_BODY_TEXT_SIZE = 31
ACTION_BODY_TEXT_H = 37

ACTION_FLAVOR_L = 275
ACTION_FLAVOR_R = 100
ACTION_FLAVOR_LINE_Y = 559
ACTION_FLAVOR_DY = 14
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

PUBLIC_TITLE_L = 250
PUBLIC_TITLE_R = 100
PUBLIC_TITLE_Y1 = 35
PUBLIC_TITLE_Y2 = 15
PUBLIC_TITLE_TEXT_SIZE = 44
PUBLIC_TITLE_TEXT_H = 44

PUBLIC_BODY_L = 250
PUBLIC_BODY_R = 50
PUBLIC_BODY_Y = 395
PUBLIC_BODY_TEXT_SIZE = 39
PUBLIC_BODY_TEXT_H = 48

AGENDA_TITLE_L = 250
AGENDA_TITLE_R = 100
AGENDA_TITLE_Y1 = 55
AGENDA_TITLE_Y2 = 35
AGENDA_TITLE_TEXT_SIZE = 44
AGENDA_TITLE_TEXT_H = 44

AGENDA_TYPE_L = 250
AGENDA_TYPE_R = 100
AGENDA_TYPE_Y = 165
AGENDA_TYPE_TEXT_SIZE = 31
AGENDA_TYPE_TEXT_H = 31

AGENDA_BODY_ELECT_L = 250
AGENDA_BODY_ELECT_R = 90
AGENDA_BODY_FORAGAINST_L = 60
AGENDA_BODY_FORAGAINST_R = 75
AGENDA_BODY_Y = 225
AGENDA_BODY_TEXT_SIZE = 28
AGENDA_BODY_TEXT_H = 35

# REPLACE THESE WITH PER CARD CONSTANTS
TITLE_SIZE = 44
TITLE_LINEH = 44
TYPE_SIZE = 32
TYPE_LINEH = 32
BODY_SM_SIZE = 31
BODY_SM_LINEH = 37
BODY_LG_SIZE = 40
BODY_LG_LINEH = 47

def actionCard(title, body, flavor, isCodex):
    img = getImage('ActionCardCodex.jpg' if isCodex else 'ActionCard.jpg')
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', ACTION_TITLE_TEXT_SIZE)
    color = (255, 232, 150, 255)
    text = title
    x = ACTION_TITLE_L
    y1 = ACTION_TITLE_Y1
    y2 = ACTION_TITLE_Y2
    maxX = CARD_W - ACTION_TITLE_R
    lineH = ACTION_TITLE_TEXT_H
    y = nudgeY(font, text, maxX, y1, y2)
    wrapText(draw, font, text, x, y, maxX, color, lineH)

    font1 = getFont('MyriadProBold.ttf', ACTION_BODY_TEXT_SIZE)
    font2 = getFont('MyriadProSemibold.otf', ACTION_BODY_TEXT_SIZE)
    color = (255, 255, 255, 255)
    text = body
    x = ACTION_BODY_L
    y = ACTION_BODY_Y
    maxX = CARD_W - ACTION_BODY_R
    lineH = ACTION_BODY_TEXT_H
    for line in text.split('\n'):
        y = wrapTextBoldStart(draw, font1, font2, line, x, y, maxX, color, lineH)

    y = max(y, ACTION_FLAVOR_LINE_Y)
    draw.line([(107, y), (CARD_W - 69, y)], fill=(255, 255, 255, 255), width=3)


    font = getFont('MyriadWebProItalic.ttf', ACTION_FLAVOR_TEXT_SIZE)
    color = (255, 255, 255, 255)
    text = flavor
    x = ACTION_FLAVOR_L
    y = y + ACTION_FLAVOR_DY
    maxX = CARD_W - ACTION_FLAVOR_R
    lineH = ACTION_FLAVOR_TEXT_H
    for line in text.split('\n'):
        y = wrapTextCenter(draw, font, line, x, y, maxX, color, lineH)

    #img2 = getImage('Bribery.jpg')
    #img.putalpha(1)
    #img2.putalpha(1)
    #img = Image.blend(img, img2, 0.4)
    #img = img.convert('RGB')

    return imageToJPEG(img)

def secretObjectiveCard(title, type, body):
    img = getImage('SecretObjective.jpg')
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', SECRET_TITLE_TEXT_SIZE)
    color = (254, 196, 173, 255)
    text = title
    x = SECRET_TITLE_L
    y1 = SECRET_TITLE_Y1
    y2 = SECRET_TITLE_Y2
    maxX = CARD_W - SECRET_TITLE_R
    lineH = SECRET_TITLE_TEXT_H
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    x = 125
    y = 130
    w = 250
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('HandelGothicDBold.otf', SECRET_TYPE_TEXT_SIZE)
    color = (255, 255, 255, 255) if type.lower() == 'status phase' else (255, 0, 0, 255)
    text = type
    x = SECRET_TYPE_L
    y = SECRET_TYPE_Y
    maxX = CARD_W - SECRET_TYPE_R
    lineH = SECRET_TYPE_TEXT_H
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProSemibold.otf', SECRET_BODY_TEXT_SIZE)
    color = (255, 255, 255, 255)
    text = body
    x = SECRET_BODY_L
    y = SECRET_BODY_Y
    maxX = CARD_W - SECRET_BODY_R
    lineH = BODY_LG_LINEH
    y = wrapTextCenterHV(draw, font, text, x, y, maxX, color, lineH)

    return imageToJPEG(img)

def publicObjectiveCard(level, title, body):
    imageName = 'Stage' + str(level) + '.jpg'
    img = getImage(imageName)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', PUBLIC_TITLE_TEXT_SIZE)
    color = (249, 249, 169, 255) if level == 1 else (173, 239, 254, 255)
    text = title
    x = PUBLIC_TITLE_L
    y1 = PUBLIC_TITLE_Y1
    y2 = PUBLIC_TITLE_Y2
    maxX = CARD_W - PUBLIC_TITLE_R
    lineH = PUBLIC_TITLE_TEXT_H
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProSemibold.otf', PUBLIC_BODY_TEXT_SIZE)
    color = (255, 255, 255, 255)
    text = body
    x = PUBLIC_BODY_L
    y = PUBLIC_BODY_Y
    maxX = CARD_W - PUBLIC_BODY_R
    lineH = PUBLIC_BODY_TEXT_H
    y = wrapTextCenterHV(draw, font, text, x, y, maxX, color, lineH)

    return imageToJPEG(img)

def agendaCard(title, type, body):
    img = getImage('Agenda.jpg')
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', AGENDA_TITLE_TEXT_SIZE)
    color = (149, 202, 255, 255)
    text = title
    x = AGENDA_TITLE_L
    y1 = AGENDA_TITLE_Y1
    y2 = AGENDA_TITLE_Y2
    maxX = CARD_W - AGENDA_TITLE_R
    lineH = AGENDA_TITLE_TEXT_H
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    x = 200
    y = 160
    w = 100
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('MyriadProBold.ttf', AGENDA_TYPE_TEXT_SIZE)
    color = (255, 255, 0, 255) if type.lower() == 'directive' else (221, 173, 99, 255)
    text = type
    x = AGENDA_TYPE_L
    y = AGENDA_TYPE_Y
    maxX = CARD_W - AGENDA_TYPE_R
    lineH = AGENDA_TYPE_TEXT_H
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    #font1 = getFont('MyriadProBold.ttf', AGENDA_BODY_TEXT_SIZE)
    #font2 = getFont('MyriadProSemibold.otf', AGENDA_BODY_TEXT_SIZE)
    font2 = getFont('MyriadProRegular.ttf', AGENDA_BODY_TEXT_SIZE)
    color = (0, 0, 0, 255)
    text = body
    y = AGENDA_BODY_Y
    lineH = AGENDA_BODY_TEXT_H
    if 'Elect ' in text:
        font1 = getFont('MyriadProSemibold.otf', AGENDA_BODY_TEXT_SIZE)
        x = AGENDA_BODY_ELECT_L
        maxX = CARD_W - AGENDA_BODY_ELECT_R
        for line in text.split('\n'):
            if line.startswith('Elect '):
                y = wrapTextCenter(draw, font1, line, x, y, maxX, color, lineH)
            else:
                y = wrapTextCenter(draw, font2, line, x, y, maxX, color, lineH)
    else:
        font1 = getFont('MyriadProSemiboldItalic.ttf', AGENDA_BODY_TEXT_SIZE)
        x = AGENDA_BODY_FORAGAINST_L
        maxX = CARD_W - AGENDA_BODY_FORAGAINST_R
        for line in text.split('\n'):
            if line.startswith('For:') or line.startswith('Against:'):
                y = wrapTextBoldStart(draw, font1, font2, line, x, y, maxX, color, lineH)
            else:
                y = wrapText(draw, font2, line, x, y, maxX, color, lineH)

    return imageToJPEG(img)

def nobilityCard(color, title, type, body, footer, points):
    filename = 'Nobility' + color + '.jpg'
    img = getImage(filename)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', TITLE_SIZE)
    color = (255, 255, 255, 255)
    text = title
    x = 250
    y1 = 35
    y2 = 15
    maxX = 400
    lineH = TITLE_LINEH
    y = nudgeY(font, text, maxX, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProBold.ttf', TYPE_SIZE)
    color = (255, 255, 255, 255) if type.lower() == 'status phase' else (255, 0, 0, 255)
    text = type
    x = 250
    y = 135
    maxX = 400
    lineH = TYPE_LINEH
    wrapTextCenter(draw, font, text, x, y, maxX, color, lineH)

    font = getFont('MyriadProSemibold.otf', BODY_LG_SIZE)
    color = (255, 255, 255, 255)
    text = body
    x = 250
    y = 375
    maxX = 450
    lineH = BODY_LG_LINEH
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
        hash.update('version5')
        key = hash.hexdigest().lower()

        jpg = memcache.get(key=key)
        #jpg = None
        if jpg is None:
            if card == 'action':
                jpg = actionCard(title, body, flavor, False)
            elif card == 'action_codex':
                jpg = actionCard(title, body, flavor, True)
            elif card == 'secret':
                jpg = secretObjectiveCard(title, type, body)
            elif card == 'stage1':
                jpg = publicObjectiveCard(1, title, body)
            elif card == 'stage2':
                jpg = publicObjectiveCard(2, title, body)
            elif card == 'agenda':
                jpg = agendaCard(title, type, body)
            elif card == 'nobility':
                jpg = nobilityCard(color, title, type, body, footer, points)
            else:
                self.response.status = 400 # bad request
                self.response.status_message = 'Bad card type'
                self.response.out.write('Bad card type "' + card + '"')
                return
            memcache.add(key, jpg, 3600)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

class TestActionHandler(webapp2.RequestHandler):
    def get(self):
        title = 'Bribery'
        body = 'After the speaker votes on an agenda: Spend any number of trade goods. For each trade good spent, cast 1 additional vote for any outcome.'
        flavor = u'\u201CWe think that this initiative would spell disaster for the galaxy, not just the Creuss.\u201D Taivra said, quietly slipping Z\u2018eu an envelope. \u201CDon\u2019t you agree?\u201D'
        jpg = actionCard(title.upper(), body, flavor, False)
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

app = webapp2.WSGIApplication([
    ('/img', CardHandler),
    ('/testaction', TestActionHandler),
    ('/testsecret', TestSecretHandler),
    ('/testpublic', TestPublicHandler),
    ('/testagenda', TestAgenda1Handler),
    ('/testagenda2', TestAgenda2Handler),

], debug=True)
