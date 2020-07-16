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

PARAGRAPH_LINE_HEIGHT_SCALE = 1.75

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

def nudgeY(font, text, maxWidth, y1, y2):
    (w, h) = font.getsize(text)
    return y1 if w <= maxWidth else y2

# -----------------------------------------------------------------------------

def wrapText(draw, font, text, x, y, maxWidth, fill):
    (spaceW, h) = font.getsize(' ')
    lineH = h + 10
    words = text.split(' ')
    text = ''
    lineWidth = 0
    for word in words:
        (w, h) = font.getsize(word)
        if lineWidth + w > maxWidth:
            draw.text((x, y), text, font=font, fill=fill)
            text = ''
            lineWidth = 0
            y += lineH
        text += word + ' '
        lineWidth += w + spaceW
    draw.text((x, y), text, font=font, fill=fill)
    return y + (lineH * PARAGRAPH_LINE_HEIGHT_SCALE)

def wrapTextCenter(draw, font, text, x, y, maxWidth, fill):
    (spaceW, h) = font.getsize(' ')
    lineH = h + 10
    words = text.split(' ')
    text = ''
    lineWidth = 0
    for word in words:
        (w, h) = font.getsize(word)
        if lineWidth + w > maxWidth:
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

def wrapTextCenterHV(draw, font, text, x, y, maxWidth, fill):
    text = text.replace('\n', ' \n ')
    lines = []
    (spaceW, h) = font.getsize(' ')
    lineH = h + 10
    words = text.split(' ')
    text = ''
    lineWidth = 0
    for word in words:
        (w, h) = font.getsize(word)
        if word == '\n' or lineWidth + w > maxWidth:
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

def wrapTextBoldStart(draw, font1, font2, text, x, y, maxWidth, fill):
    font = font1
    (spaceW, spaceH) = font.getsize(' ')
    lineH = spaceH + 10
    words = text.split(' ')
    text = ''
    startX = x
    indent = 0
    for word in words:
        (w, h) = font.getsize(word)
        if x + w > maxWidth:
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

def actionCard(title, body, flavor):
    img = getImage('ActionCard.jpg')
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', 44)
    color = (255, 232, 150, 255)
    text = title
    x = 85
    y1 = 92
    y2 = 72
    maxWidth = 400
    y = nudgeY(font, text, maxWidth, y1, y2)
    wrapText(draw, font, text, x, y, maxWidth, color)

    font1 = getFont('MyriadProBold.ttf', 36)
    font2 = getFont('MyriadProSemibold.otf', 36)
    color = (255, 255, 255, 255)
    text = body
    x = 60
    y = 200
    maxWidth = 480
    for line in text.split('\n'):
        y = wrapTextBoldStart(draw, font1, font2, line, x, y, maxWidth, color)

    font = getFont('MyriadWebProItalic.ttf', 30)
    color = (255, 255, 255, 255)
    text = flavor
    x = 270
    y = 575
    maxWidth = 425
    for line in text.split('\n'):
        y = wrapTextCenter(draw, font, line, x, y, maxWidth, color)

    return imageToJPEG(img)

def secretObjectiveCard(title, type, body):
    img = getImage('SecretObjective.jpg')
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', 44)
    color = (254, 196, 173, 255)
    text = title
    x = 250
    y1 = 35
    y2 = 15
    maxWidth = 400
    y = nudgeY(font, text, maxWidth, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    x = 125
    y = 130
    w = 250
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('HandelGothicDBold.otf', 32)
    color = (255, 255, 255, 255) if type.lower() == 'status phase' else (255, 0, 0, 255)
    text = type
    x = 250
    y = 130
    maxWidth = 400
    wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    font = getFont('MyriadProSemibold.otf', 36)
    color = (255, 255, 255, 255)
    text = body
    x = 250
    y = 375
    maxWidth = 450
    y = wrapTextCenterHV(draw, font, text, x, y, maxWidth, color)

    return imageToJPEG(img)

def publicObjectiveCard(level, title, body):
    imageName = 'Stage' + str(level) + '.jpg'
    img = getImage(imageName)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', 44)
    color = (249, 249, 169, 255) if level == 1 else (173, 239, 254, 255)
    text = title
    x = 250
    y1 = 35
    y2 = 15
    maxWidth = 400
    y = nudgeY(font, text, maxWidth, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    font = getFont('MyriadProSemibold.otf', 36)
    color = (255, 255, 255, 255)
    text = body
    x = 250
    y = 375
    maxWidth = 450
    y = wrapTextCenterHV(draw, font, text, x, y, maxWidth, color)

    return imageToJPEG(img)

def agendaCard(title, type, body):
    img = getImage('Agenda.jpg')
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', 44)
    color = (255, 255, 255, 255)
    text = title
    x = 250
    y1 = 35
    y2 = 15
    maxWidth = 400
    y = nudgeY(font, text, maxWidth, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    x = 200
    y = 160
    w = 100
    h = 30
    color = (12, 12, 14, 255)
    draw.rectangle([(x, y), (x+w, y+h)], color)

    font = getFont('MyriadProBold.ttf', 30)
    color = (255, 255, 0, 255) if type.lower() == 'directive' else (221, 173, 99, 255)
    text = type
    x = 250
    y = 165
    maxWidth = 400
    wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    font1 = getFont('MyriadProBold.ttf', 30)
    font2 = getFont('MyriadProSemibold.otf', 30)
    color = (0, 0, 0, 255)
    text = body
    y = 220
    maxWidth = 480
    if 'Elect ' in text:
        for line in text.split('\n'):
            x = 250
            if line.startswith('Elect '):
                y = wrapTextCenter(draw, font1, line, x, y, maxWidth, color)
            else:
                y = wrapTextCenter(draw, font2, line, x, y, maxWidth, color)
    else:
        x = 60
        for line in text.split('\n'):
            if line.startswith('For:') or line.startswith('Against:'):
                y = wrapTextBoldStart(draw, font1, font2, line, x, y, maxWidth, color)
            else:
                y = wrapText(draw, font2, line, x, y, maxWidth, color)

    return imageToJPEG(img)

def nobilityCard(color, title, type, body, footer, points):
    filename = 'Nobility' + color + '.jpg'
    img = getImage(filename)
    draw = ImageDraw.Draw(img)

    font = getFont('HandelGothicDBold.otf', 44)
    color = (255, 255, 255, 255)
    text = title
    x = 250
    y1 = 35
    y2 = 15
    maxWidth = 400
    y = nudgeY(font, text, maxWidth, y1, y2)
    wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    font = getFont('MyriadProBold.ttf', 30)
    color = (255, 255, 255, 255) if type.lower() == 'status phase' else (255, 0, 0, 255)
    text = type
    x = 250
    y = 135
    maxWidth = 400
    wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    font = getFont('MyriadProSemibold.otf', 36)
    color = (255, 255, 255, 255)
    text = body
    x = 250
    y = 375
    maxWidth = 450
    y = wrapTextCenterHV(draw, font, text, x, y, maxWidth, color)

    font = getFont('MyriadProBold.ttf', 40)
    color = (255, 255, 255, 255) if footer.lower() == 'public' else (255, 0, 0, 255)
    text = footer
    x = 250
    y = 520
    maxWidth = 450
    y = wrapTextCenter(draw, font, text, x, y, maxWidth, color)

    font = getFont('HandelGothicDBold.otf', 130)
    color = (255, 255, 255, 255)
    text = str(points)
    x = 265
    y = 565
    maxWidth = 450
    y = wrapTextCenter(draw, font, text, x, y, maxWidth, color)

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
        hash.update(card)
        hash.update(title)
        hash.update(type)
        hash.update(body)
        hash.update(footer)
        hash.update(flavor)
        hash.update(color)
        hash.update(points)
        key = hash.hexdigest().lower()

        jpg = memcache.get(key=key)
        #jpg = None
        if jpg is None:
            if card == 'action':
                jpg = actionCard(title, body, flavor)
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
                return
            memcache.add(key, jpg, 3600)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(jpg)

app = webapp2.WSGIApplication([
    ('/img', CardHandler),
], debug=True)
