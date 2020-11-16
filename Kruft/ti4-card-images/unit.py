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

def unitCard(content, prereqs, stats, titlesize, fontsize):
    img = getImage('jaheit_unit_upgrade/background.jpg')
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Solid block, use alpha blend with an overlay.
    subtitleColor = content['subtitleColor']
    solid = Image.new('RGBA', (CARD_W, CARD_H), ImageColor.getrgb('#' + subtitleColor))

    # UNIT IMAGE
    unitImage = content['unitImage']
    if unitImage and len(unitImage) > 0:
        overlay = getImage('jaheit_unit_upgrade/' + unitImage)
        img.paste(overlay, (0, 0), overlay)

    # FACTION
    factionImage = content['factionImage']
    if factionImage != '' and factionImage != 'BLANK':
        factionImg = getImage('faction_icons/' + factionImage)
        factionImg = factionImg.resize((200, 200))
        img.paste(factionImg, (-40, -45), factionImg)

    # TITLE
    title = content['title']
    titleLeft = 60 if factionImage == '' else 120
    color = (255, 255, 255, 255)
    font = FontData('HandelGothicDBold.otf', 39 + titlesize, color)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBounds(titleLeft, 0, CARD_W - 60, 70)
    textBlock.setLineHeight(font._fontSize + titlesize)
    textBlock.setCenterV(True)
    textBlock.setText(title)
    textBlock.draw(draw)
    generates = stats['generates']
    if generates and len(generates) > 0:
        if generates == 'green':
            color = ImageColor.getrgb('#178414')
        elif generates == 'blue':
            color = ImageColor.getrgb('#95caff')
        elif generates == 'red':
            color = ImageColor.getrgb('#b93340')
        elif generates == 'yellow':
            color = ImageColor.getrgb('#e5dc76')
        textBlock.drawGradient(img, color, (255, 255, 255, 255))

    # SUBTITLE
    subtitle = content['subtitle']
    subtitleColor = content['subtitleColor']
    if subtitle and len(subtitle) > 0:
        color = ImageColor.getrgb('#' + subtitleColor)
        font = FontData('HandelGothicDBold.otf', 26, color)
        textBlock = TextBlock()
        textBlock.setFont(font)
        textBlock.setBounds(titleLeft, 70, CARD_W - 60, 115)
        textBlock.setLineHeight(font._fontSize + titlesize)
        textBlock.setCenterV(True)
        textBlock.setText(subtitle)
        textBlock.draw(draw)

    # BODY
    body = content['body']
    top = 135 if subtitle == '' else 135
    font = FontData('MyriadProSemibold.otf', 31 + fontsize, (255, 255, 255, 255))
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBounds(100, top, CARD_W - 50, CARD_H - 25)
    textBlock.setLineHeight(font._fontSize + fontsize)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setText(body)
    y, h = textBlock.draw(draw)

    # ATTRIBUTES
    attributes = content['attributes']
    top = y + 15
    font = FontData('HandelGothicDBold.otf', 28 + fontsize, (255, 255, 255, 255))
    overrideFont = FontData('PierreDingbats.ttf', 24 + fontsize, (255, 255, 255, 255))
    overrideFont.setOffset(4)
    textBlock = TextBlock()
    textBlock.setFont(font)
    textBlock.setBounds(100, top, CARD_W - 50, 325)
    textBlock.setLineHeight(font._fontSize + fontsize)
    textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
    textBlock.setAlignBottom(True)
    textBlock.setText(attributes.replace('* ', 'F '))
    textBlock.setOverride({'F'}, overrideFont)
    textBlock.draw(draw)

    # PREREQ FRAME
    prereqCount = prereqs['r'] + prereqs['y'] + prereqs['b'] + prereqs['g']
    if prereqCount > 0 and prereqCount <= 4:
        frameImg = getImage('jaheit_unit_upgrade/prereq_' + str(prereqCount) + '.png')
        img.paste(frameImg, (0, 0), frameImg)

    # PREREQS
    w, h = 55, 77
    x = 15
    y = 500 - h - 7
    if prereqs['r'] > 0:
        preImg = getImage('jaheit_unit_upgrade/prereq_red.png')
        ix = x + w / 2
        iw, ih = preImg.size
        for _ in range(prereqs['r']):
            iy = y + h / 2
            img.paste(preImg, (ix - iw / 2, iy - ih / 2), preImg)
            y -= h
    if prereqs['y'] > 0:
        preImg = getImage('jaheit_unit_upgrade/prereq_yellow.png')
        ix = x + w / 2
        iw, ih = preImg.size
        for _ in range(prereqs['y']):
            iy = y + h / 2
            img.paste(preImg, (ix - iw / 2, iy - ih / 2), preImg)
            y -= h
    if prereqs['b'] > 0:
        preImg = getImage('jaheit_unit_upgrade/prereq_blue.png')
        ix = x + w / 2
        iw, ih = preImg.size
        for _ in range(prereqs['b']):
            iy = y + h / 2
            img.paste(preImg, (ix - iw / 2, iy - ih / 2), preImg)
            y -= h
    if prereqs['g'] > 0:
        preImg = getImage('jaheit_unit_upgrade/prereq_green.png')
        ix = x + w / 2
        iw, ih = preImg.size
        for _ in range(prereqs['g']):
            iy = y + h / 2
            img.paste(preImg, (ix - iw / 2, iy - ih / 2), preImg)
            y -= h

    # BOTTOM COST
    fontValue = FontData('HandelGothicDBold.otf', 100, (255, 255, 255, 255))
    fontLabel = FontData('HandelGothicDBold.otf', 26, (255, 255, 255, 255))
    cost = stats['cost']
    if cost > 0:
        overlay = getImage('jaheit_unit_upgrade/bot_cost.png')
        img.paste(solid, (0, 0), overlay)
        img.paste(solid, (0, 0), overlay)  # again, for better visibility

        left = 88
        right = left + 162
        textBlock = TextBlock()
        textBlock.setFont(fontLabel)
        textBlock.setBounds(left, 450, right, 475)
        textBlock.setLineHeight(fontLabel._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText('COST')
        textBlock.draw(draw)

        if content['unitImage'] == 'bg_fighter.png':
            right -= 30
            x2 = getImage('jaheit_unit_upgrade/bot_cost_fighter_x2.png')
            img.paste(x2, (25, 0), x2)
        if content['unitImage'] == 'bg_infantry.png':
            right -= 30
            x2 = getImage('jaheit_unit_upgrade/bot_cost_infantry_x2.png')
            img.paste(x2, (25, 0), x2)

        textBlock = TextBlock()
        textBlock.setFont(fontValue)
        textBlock.setBounds(left, 335, right, 442)
        textBlock.setLineHeight(fontValue._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText(str(cost))
        textBlock.draw(draw)

    # BOTTOM COMBAT
    combat = stats['combat']
    combatDice = stats['combatDice']
    if combat > 0:
        overlay = getImage('jaheit_unit_upgrade/bot_combat.png')
        img.paste(solid, (0, 0), overlay)
        img.paste(solid, (0, 0), overlay)  # again, for better visibility

        left = 256
        right = left + 162
        textBlock = TextBlock()
        textBlock.setFont(fontLabel)
        textBlock.setBounds(left, 450, right, 475)
        textBlock.setLineHeight(fontLabel._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText('COMBAT')
        textBlock.draw(draw)

        if combatDice == 2:
            right -= 30
            x2 = getImage('jaheit_unit_upgrade/bot_combat_x2.png')
            img.paste(x2, (0, 0), x2)
        if combatDice == 3:
            right -= 30
            x2 = getImage('jaheit_unit_upgrade/bot_combat_x3.png')
            img.paste(x2, (0, 0), x2)

        textBlock = TextBlock()
        textBlock.setFont(fontValue)
        textBlock.setBounds(left, 335, right, 442)
        textBlock.setLineHeight(fontValue._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText(str(combat))
        textBlock.draw(draw)

    # BOTTOM MOVE
    move = stats['move']
    if move > 0:
        overlay = getImage('jaheit_unit_upgrade/bot_move.png')
        img.paste(solid, (0, 0), overlay)
        img.paste(solid, (0, 0), overlay)  # again, for better visibility

        left = 424
        right = left + 162
        textBlock = TextBlock()
        textBlock.setFont(fontLabel)
        textBlock.setBounds(left, 450, right, 475)
        textBlock.setLineHeight(fontLabel._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText('MOVE')
        textBlock.draw(draw)

        textBlock = TextBlock()
        textBlock.setFont(fontValue)
        textBlock.setBounds(left, 335, right, 442)
        textBlock.setLineHeight(fontValue._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText(str(move))
        textBlock.draw(draw)

    # BOTTOM CAPACITY
    capacity = stats['capacity']
    if capacity > 0:
        overlay = getImage('jaheit_unit_upgrade/bot_capacity.png')
        img.paste(solid, (0, 0), overlay)
        img.paste(solid, (0, 0), overlay)  # again, for better visibility

        left = 593
        right = left + 162
        textBlock = TextBlock()
        textBlock.setFont(fontLabel)
        textBlock.setBounds(left, 450, right, 475)
        textBlock.setLineHeight(fontLabel._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText('CAPACITY')
        textBlock.draw(draw)

        textBlock = TextBlock()
        textBlock.setFont(fontValue)
        textBlock.setBounds(left, 335, right, 442)
        textBlock.setLineHeight(fontValue._fontSize)
        textBlock.setNewlineScale(PARAGRAPH_LINE_HEIGHT_SCALE)
        textBlock.setCenterH(True)
        textBlock.setText(str(capacity))
        textBlock.draw(draw)

    # BOTTOM GENERATES -- OR -- SPACER
    generates = stats['generates']
    if generates and len(generates) > 0:
        overlay = getImage('jaheit_unit_upgrade/generate_' + generates + '.png')
        img.paste(overlay, (0, 0), overlay)
    else:
        botSpacer = False
        if cost == 0 and combat == 0 and move == 0 and capacity == 0:
            botSpacer = 'jaheit_unit_upgrade/bot_spacer_4.png'
        elif move == 0 and capacity == 0:
            botSpacer = 'jaheit_unit_upgrade/bot_spacer_2.png'
        elif capacity == 0:
            botSpacer = 'jaheit_unit_upgrade/bot_spacer_1.png'
        if botSpacer:
            overlay = getImage(botSpacer)
            img.paste(solid, (0, 0), overlay)
            img.paste(solid, (0, 0), overlay)  # again, for better visibility

    img = img.convert('RGB')
    return imageToJPEG(img)

#------------------------------------------------------------------------------

class UnitHandler(webapp2.RequestHandler):
    def get(self):
        title = self.request.get('title', '').upper()
        subtitle = self.request.get('subtitle', '').upper()
        subtitleColor = self.request.get('subtitleColor', '').upper()
        factionImage = self.request.get('factionImage', '')
        attributes = self.request.get('attributes', '')
        body = self.request.get('body', '')
        unitImage = self.request.get('unitImage', '')
        prereqGreen = self.request.get('prereqGreen', '0')
        prereqBlue = self.request.get('prereqBlue', '0')
        prereqYellow = self.request.get('prereqYellow', '0')
        prereqRed = self.request.get('prereqRed', '0')
        generates = self.request.get('generates', '0')
        cost = self.request.get('cost', '0')
        combat = self.request.get('combat', '0')
        combatDice = self.request.get('combatDice', '0')
        move = self.request.get('move', '0')
        capacity = self.request.get('capacity', '0')
        titlesize = self.request.get('titlesize', '0')
        fontsize = self.request.get('fontsize', '0')

        hash = hashlib.sha256()
        hash.update(title.encode('utf-8'))
        hash.update(subtitle.encode('utf-8'))
        hash.update(subtitleColor.encode('utf-8'))
        hash.update(factionImage.encode('utf-8'))
        hash.update(attributes.encode('utf-8'))
        hash.update(body.encode('utf-8'))
        hash.update(unitImage.encode('utf-8'))
        hash.update(prereqGreen.encode('utf-8'))
        hash.update(prereqBlue.encode('utf-8'))
        hash.update(prereqGreen.encode('utf-8'))
        hash.update(prereqYellow.encode('utf-8'))
        hash.update(prereqRed.encode('utf-8'))
        hash.update(generates.encode('utf-8'))
        hash.update(cost.encode('utf-8'))
        hash.update(combat.encode('utf-8'))
        hash.update(combatDice.encode('utf-8'))
        hash.update(move.encode('utf-8'))
        hash.update(capacity.encode('utf-8'))
        hash.update(titlesize.encode('utf-8'))
        hash.update(fontsize.encode('utf-8'))
        hash.update('version1')
        key = hash.hexdigest().lower()

        content = {
            'title' : title,
            'subtitle' : subtitle,
            'subtitleColor' : subtitleColor,
            'factionImage' : factionImage,
            'attributes' : attributes,
            'body' : body,
            'unitImage' : unitImage
        }
        prereqs = {
            'g' : int(prereqGreen),
            'b' : int(prereqBlue),
            'y' : int(prereqYellow),
            'r' : int(prereqRed)
        }
        stats = {
            'cost' : int(cost),
            'combat' : int(combat),
            'combatDice' : int(combatDice),
            'move' : int(move),
            'capacity' : int(capacity),
            'generates' : generates
        }
        titlesize = int(titlesize)
        fontsize = int(fontsize)

        jpg = memcache.get(key=key)
        #jpg = None
        if jpg is None:
            jpg = unitCard(content, prereqs, stats, titlesize, fontsize)
            memcache.add(key, jpg, 3600)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)
