#!/usr/bin/env python
# -*- coding: latin-1 -*-


# dev_appserver.py app.yaml
# gcloud app deploy app.yaml --project ti4-card-images
"""
"""

from textLayout import FontData
from textLayout import TextBlock

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

PARAGRAPH_LINE_HEIGHT_SCALE = 1.5

# -----------------------------------------------------------------------------

def getImage(name):
    dir = os.path.dirname(__file__)
    static = os.path.join(dir, 'static')
    file = os.path.join(static, name)
    return Image.open(file)

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

ELECT_WORDS = {
    'Elect',
    unicode('Élisez', 'utf-8'),
}

FOR_AGAINST_WORDS = {
    'For',
    'Against',
    unicode('Pour', 'utf-8'),
    unicode('Contre', 'utf-8'),
}

CARD_W = 500
CARD_H = 750

# -----------------------------------------------------------------------------

def actionCard(title, body, flavor, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    # TITLE
    font = FontData('HandelGothicDBold.otf', 39 + titlesize, (255, 232, 150, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBounds(85, 70, CARD_W - 30, 150)
    textBlock.setLineHeight(39 + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)

    # BODY
    body = body.replace('Action:', 'ACTION:')
    body = body.replace('Action :', 'ACTION :')
    font = FontData('MyriadProSemibold.otf', 31 + fontsize, (255, 255, 255, 255))
    boldStartFont = False
    if body.startswith('ACTION'):
        boldStartFont = FontData('MyriadProBoldItalic.ttf', 31 + fontsize, (255, 255, 255, 255))
    else:
        boldStartFont = FontData('MyriadProBold.ttf', 31 + fontsize, (255, 255, 255, 255))
    overrideFont = FontData('HandelGothicDBold.otf', 24 + fontsize, (255, 255, 255, 255))
    overrideFont.applyOffset(font)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBoldStart(boldStartFont)
    textBlock.setOverride(FONT_3_WORDS, overrideFont)
    textBlock.setBounds(70, 206, CARD_W - 25, CARD_H - 25)
    textBlock.setLineHeight(37 + fontsize)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(body)
    textBlock.draw(draw)

    # FLAVOR
    font = FontData('MyriadWebProItalic.ttf', 27 + fontsize, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setAlignBottom(True)
    textBlock.setBounds(70, 206, CARD_W - 25, CARD_H - 25)
    textBlock.setLineHeight(31 + fontsize)
    textBlock.setText(flavor)
    y, h = textBlock.draw(draw)
    y = (y - h) - 15
    draw.line([(107, y), (CARD_W - 69, y)], fill=(255, 255, 255, 255), width=2)

    return imageToJPEG(img)

def secretObjectiveCard(title, type, body, footer, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    x = 125
    y = 130
    w = 250
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    x = 125
    y = 710
    w = 250
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    # TITLE
    font = FontData('HandelGothicDBold.otf', 39 + titlesize, (254, 196, 173, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(30, 20, CARD_W - 30, 100)
    textBlock.setLineHeight(39 + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)

    # TYPE
    items = type.split('|')
    type = items[0]
    color = ImageColor.getrgb('#' + items[1])
    font = FontData('HandelGothicDBold.otf', 31, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(125, 130, 375, 160)
    textBlock.setLineHeight(31)
    textBlock.setText(type)
    textBlock.draw(draw)

    # BODY
    font = FontData('MyriadProSemibold.otf', 38 + fontsize, (255, 255, 255, 255))
    overrideFont = FontData('HandelGothicDBold.otf', 32 + fontsize, (255, 255, 255, 255))
    overrideFont.applyOffset(font)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setOverride(FONT_3_WORDS, overrideFont)
    textBlock.setCenterH(True)
    textBlock.setCenterV(True)
    textBlock.setBounds(25, 206, CARD_W - 25, 560)
    textBlock.setLineHeight(47 + fontsize)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(body)
    y, h = textBlock.draw(draw)

    # FOOTER
    items = footer.split('|')
    footer = items[0]
    color = ImageColor.getrgb('#' + items[1])
    font = FontData('HandelGothicDBold.otf', 30, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(125, 705, 375, 740)
    textBlock.setLineHeight(30)
    textBlock.setText(footer)
    y, h = textBlock.draw(draw)

    return imageToJPEG(img)

def publicObjectiveCard(level, title, type, body, footer, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    x = 125
    y = 130
    w = 250
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    x = 100
    y = 710
    w = 300
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    # TITLE
    color = (249, 249, 169, 255) if level == 1 else (173, 239, 254, 255)
    font = FontData('HandelGothicDBold.otf', 43 + titlesize, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(30, 20, CARD_W - 30, 100)
    textBlock.setLineHeight(43 + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)

    # TYPE
    items = type.split('|')
    type = items[0]
    color = ImageColor.getrgb('#' + items[1])
    font = FontData('HandelGothicDBold.otf', 31, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(125, 130, 375, 160)
    textBlock.setLineHeight(31)
    textBlock.setText(type)
    textBlock.draw(draw)

    # BODY
    font = FontData('MyriadProSemibold.otf', 39 + fontsize, (255, 255, 255, 255))
    overrideFont = FontData('HandelGothicDBold.otf', 33 + fontsize, (255, 255, 255, 255))
    overrideFont.applyOffset(font)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setOverride(FONT_3_WORDS, overrideFont)
    textBlock.setCenterH(True)
    textBlock.setCenterV(True)
    textBlock.setBounds(25, 206, CARD_W - 25, 560)
    textBlock.setLineHeight(48 + fontsize)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(body)
    y, h = textBlock.draw(draw)

    # FOOTER
    items = footer.split('|')
    footer = items[0]
    color = ImageColor.getrgb('#' + items[1])
    font = FontData('HandelGothicDBold.otf', 32, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(100, 705, 400, 740)
    textBlock.setLineHeight(32)
    textBlock.setText(footer)
    y, h = textBlock.draw(draw)

    return imageToJPEG(img)

def agendaCard(title, type, body, cardImage, titlesize, fontsize):
    img = getImage(cardImage)
    draw = ImageDraw.Draw(img)

    x = 200
    y = 160
    w = 100
    h = 30
    color = (24, 26, 25, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    # TITLE
    font = FontData('HandelGothicDBold.otf', 44 + titlesize, (149, 202, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(30, 40, CARD_W - 30, 120)
    textBlock.setLineHeight(44 + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)

    # TYPE
    items = type.split('|')
    type = items[0]
    color = ImageColor.getrgb('#' + items[1])
    font = FontData('HandelGothicDBold.otf', 31, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(150, 160, 350, 190)
    textBlock.setLineHeight(31)
    textBlock.setText(type)
    textBlock.draw(draw)

    # BODY
    font = FontData('MyriadProRegular.ttf', 28 + fontsize, (0, 0, 0, 255))
    overrideFont = FontData('HandelGothicDBold.otf', 24 + fontsize, (0, 0, 0, 255))
    overrideFont.applyOffset(font)
    y = 225

    # Tolerate odd spreadsheet text syntax.
    if '(When' in body:
        i = body.find('(When')
        j = body.find(')', i + 1)
        whenText = body[i+1:j]
        if len(body) > j+ 1 and body[j+1] == '\n':
            j += 1
        body = body[:i] + body[j+1:]
        textBlock = TextBlock()
        textBlock.setCenterH(True)
        textBlock.setFont(font)
        textBlock.setBounds(50, y, CARD_W - 50, 700)
        textBlock.setLineHeight(37 + fontsize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setText(whenText)
        y, _ = textBlock.draw(draw)
        y += textBlock._lineH * (PARAGRAPH_LINE_HEIGHT_SCALE - 1)

    electFr = unicode('Élisez ', 'utf-8')
    if ('Elect ' in body) or (electFr in body):
        boldFont = FontData('MyriadProSemibold.otf', 28 + fontsize, (0, 0, 0, 255))
        for line in body.split('\n'):
            textBlock = TextBlock()
            textBlock.setCenterH(True)
            textBlock.setFont(font)
            textBlock.setOverride(FONT_3_WORDS, overrideFont)
            textBlock.setBounds(50, y, CARD_W - 50, 700)
            textBlock.setLineHeight(37 + fontsize)
            textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
            if line.startswith('Elect ') or line.startswith(electFr):
                textBlock.setFont(boldFont)
            textBlock.setText(line.strip())
            y, _ = textBlock.draw(draw)
            y += textBlock._lineH * (PARAGRAPH_LINE_HEIGHT_SCALE - 1)
    else:
        startFont = FontData('MyriadProSemiboldItalic.ttf', 28 + fontsize, (0, 0, 0, 255))
        for line in body.split('\n'):
            isFor = line.startswith('For:') or line.startswith('Pour :')
            isAgainst = line.startswith('Against:') or line.startswith('Contre :')
            textBlock = TextBlock()
            textBlock.setFont(font)
            textBlock.setOverride(FONT_3_WORDS, overrideFont)
            textBlock.setBounds(50, y, CARD_W - 50, 700)
            textBlock.setLineHeight(37 + fontsize)
            textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
            if isFor or isAgainst:
                textBlock.setBoldStart(startFont)
                textBlock.setIndent(20)
            textBlock.setText(line.strip())
            y, _ = textBlock.draw(draw)
            y += textBlock._lineH * (PARAGRAPH_LINE_HEIGHT_SCALE - 1)

    return imageToJPEG(img)

def promissoryCard(color, title, body, titlesize, fontsize):
    filename = 'Promissory_' + color + '.jpg'
    img = getImage(filename)
    draw = ImageDraw.Draw(img)

    # TITLE
    font = FontData('HandelGothicDBold.otf', 39 + titlesize, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(30, 20, CARD_W - 30, 100)
    textBlock.setLineHeight(39 + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)

    # BODY
    font = FontData('MyriadProRegular.ttf', 31 + fontsize, (0, 0, 0, 255))
    boldFont = FontData('MyriadProBold.ttf', 31 + fontsize, (0, 0, 0, 255))
    overrideFont = FontData('HandelGothicDBold.otf', 24 + fontsize, (0, 0, 0, 255))
    overrideFont.applyOffset(font)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBoldStart(boldFont)
    textBlock.setOverride(FONT_3_WORDS, overrideFont)
    textBlock.setBounds(40, 150, CARD_W - 40, 670)
    textBlock.setLineHeight(37)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(body)
    textBlock.draw(draw)

    return imageToJPEG(img)

def nobilityCard(color, title, type, body, footer, points, titlesize, fontsize):
    filename = 'Nobility' + color + '.jpg'
    img = getImage(filename)
    draw = ImageDraw.Draw(img)

    # TITLE
    font = FontData('HandelGothicDBold.otf', 44 + titlesize, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(30, 20, CARD_W - 30, 100)
    textBlock.setLineHeight(44 + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)

    # TYPE
    items = type.split('|')
    type = items[0]
    color = ImageColor.getrgb('#' + items[1])
    font = FontData('HandelGothicDBold.otf', 31, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(125, 130, 375, 160)
    textBlock.setLineHeight(31)
    textBlock.setText(type)
    textBlock.draw(draw)

    # BODY
    font = FontData('MyriadProSemibold.otf', 39 + fontsize, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setCenterV(True)
    textBlock.setBounds(25, 206, CARD_W - 25, 560)
    textBlock.setLineHeight(48 + fontsize)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(body)
    textBlock.draw(draw)

    # FOOTER
    color = (255, 255, 255, 255) if footer.lower() == 'public' else (255, 0, 0, 255)
    font = FontData('MyriadProBold.ttf', 40, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(25, 520, CARD_W - 25, 560)
    textBlock.setLineHeight(40)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(footer)
    textBlock.draw(draw)

    # POINTS
    color = (255, 255, 255, 255) if footer.lower() == 'public' else (255, 0, 0, 255)
    font = FontData('HandelGothicDBold.otf', 130, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setCenterH(True)
    textBlock.setBounds(200, 565, 300, 700)
    textBlock.setLineHeight(130)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(points)
    textBlock.draw(draw)

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
        'cardImage' : False,
        'back' : 'Promissory_Note_Back.jpg',
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
        hash.update('version9')
        key = hash.hexdigest().lower()

        cardOptions = CARD_OPTIONS[card]
        cardType = cardOptions['cardType']
        cardImage = cardOptions['cardImage']
        titlesize = int(titlesize)
        fontsize = int(fontsize)

        jpg = memcache.get(key=key)
        jpg = None
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
        title = 'Bribery\nLine2'
        body = 'After the speaker votes on an agenda: Spend\n any BOMBARDMENT of trade goods. For each trade good spent, cast 1 additional vote for any outcome.'
        flavor = u'\u201CWe think that this initiative would spell disaster for the galaxy, not just the Creuss.\u201D Taivra said, quietly slipping Z\u2018eu an envelope. \u201CDon\u2019t you agree?\u201D'
        cardImage = 'ActionCard_c.jpg'
        titlesize = 0
        fontsize = 0
        jpg = actionCard(title.upper(), body, flavor, cardImage, titlesize, fontsize)
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
    #('/getaction', getActionHandler),
    #('/getagenda', getAgendaHandler),
    #('/testaction', TestActionHandler),
    #('/testsecret', TestSecretHandler),
    #('/testpublic', TestPublicHandler),
    #('/testagenda', TestAgenda1Handler),
    #('/testagenda2', TestAgenda2Handler),
    #('/mutatesystem', MutateSystemTile),
    #('/mutatefaction', MutateFactionTokens),
    #('/radialdither', RadialDither),
    #('/4k', FourK),
    #('/cardsheet', CardSheet),
    #('/proxy', Proxy),

], debug=False)
