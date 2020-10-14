#!/usr/bin/env python
# -*- coding: latin-1 -*-

import hashlib
import random
import os
import webapp2

from textLayout import FontData
from textLayout import TextBlock

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageColor

from google.appengine.api import memcache

#------------------------------------------------------------------------------

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

CARD_W = 750
CARD_H = 500
PARAGRAPH_LINE_HEIGHT_SCALE = 1.5

#------------------------------------------------------------------------------

def techCard(faction, title, body, preG, preB, preY, preR, generates, titlesize, fontsize):
    cardName = 'Tech_0_blank.jpg'
    count = preG + preB + preY + preR
    if count == 1:
        cardName = 'Tech_1_blank.jpg'
    if count == 2:
        cardName = 'Tech_2_blank.jpg'
    if count == 3:
        cardName = 'Tech_3_blank.jpg'

    img = getImage(cardName)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    titleLeft = 60

    # FACTION
    if faction != '':
        titleLeft = 120
        x = 0
        y = 0
        w = 120
        h = 120
        color = (12, 12, 14, 255)
        #draw.rectangle([(x, y), (x+w, y+h)], color)
        if faction != 'Blank':
            factionImg = getImage('faction_icons/' + faction)
            factionImg = factionImg.resize((200, 200))
            img.paste(factionImg, (-40, -45), factionImg)

    color = (255, 255, 255, 255)

    if generates == 'green':
        color = ImageColor.getrgb('#178414')
    elif generates == 'blue':
        color = ImageColor.getrgb('#95caff')
    elif generates == 'red':
        color = ImageColor.getrgb('#b93340')
    elif generates == 'yellow':
        color = ImageColor.getrgb('#e5dc76')

    # TITLE
    font = FontData('HandelGothicDBold.otf', 39 + titlesize, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBounds(titleLeft, 0, CARD_W - 60, 70)
    textBlock.setLineHeight(39 + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)
    textBlock.drawGradient(img, color, (255, 255, 255, 255))

    # BODY
    top = 100 if faction == '' else 100
    font = FontData('MyriadProSemibold.otf', 31 + fontsize, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBounds(110, top, CARD_W - 50, CARD_H - 25)
    textBlock.setLineHeight(37 + fontsize)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(body)
    textBlock.draw(draw)

    # GENERATES
    if generates != 'none':
        genImg = getImage('Tech_Generates_' + generates.capitalize() + '.jpg')
        w, h = 160, 160
        genImg = genImg.resize((w, h))
        img.paste(genImg, (750-w, 500-h))

    # PREREQS
    w, h = 78, 78
    x = 4
    y = 500 - h - 12
    if preR > 0:
        preImg = getImage('Tech_Prereq_Red.png')
        preImg = preImg.resize((w, h))
        for _ in range(preR):
            img.paste(preImg, (x, y), preImg)
            y -= h
    if preY > 0:
        preImg = getImage('Tech_Prereq_Yellow.png')
        preImg = preImg.resize((w, h))
        for _ in range(preY):
            img.paste(preImg, (x, y), preImg)
            y -= h
    if preB > 0:
        preImg = getImage('Tech_Prereq_Blue.png')
        preImg = preImg.resize((w, h))
        for _ in range(preB):
            img.paste(preImg, (x, y), preImg)
            y -= h
    if preG > 0:
        preImg = getImage('Tech_Prereq_Green.png')
        preImg = preImg.resize((w, h))
        for _ in range(preG):
            img.paste(preImg, (x, y), preImg)
            y -= h

    img = img.convert('RGB')
    return imageToJPEG(img)

#------------------------------------------------------------------------------

class TechHandler(webapp2.RequestHandler):
    def get(self):
        faction = self.request.get('faction', '')
        title = self.request.get('title', 'title').upper()
        body = self.request.get('body', 'body')
        prereqGreen = self.request.get('prereqGreen', '0')
        prereqBlue = self.request.get('prereqBlue', '0')
        prereqYellow = self.request.get('prereqYellow', '0')
        prereqRed = self.request.get('prereqRed', '0')
        generates = self.request.get('generates', 'none').lower()
        titlesize = self.request.get('titlesize', '0')
        fontsize = self.request.get('fontsize', '0')

        hash = hashlib.sha256()
        hash.update(faction.encode('utf-8'))
        hash.update(title.encode('utf-8'))
        hash.update(body.encode('utf-8'))
        hash.update(prereqGreen.encode('utf-8'))
        hash.update(prereqBlue.encode('utf-8'))
        hash.update(prereqGreen.encode('utf-8'))
        hash.update(prereqYellow.encode('utf-8'))
        hash.update(prereqRed.encode('utf-8'))
        hash.update(generates.encode('utf-8'))
        hash.update(titlesize.encode('utf-8'))
        hash.update(fontsize.encode('utf-8'))
        hash.update('version1')
        key = hash.hexdigest().lower()

        g = int(prereqGreen)
        b = int(prereqBlue)
        y = int(prereqYellow)
        r = int(prereqRed)
        titlesize = int(titlesize)
        fontsize = int(fontsize)

        jpg = memcache.get(key=key)
        #jpg = None
        if jpg is None:
            jpg = techCard(faction, title, body, g, b, y, r, generates, titlesize, fontsize)
            memcache.add(key, jpg, 3600)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)
