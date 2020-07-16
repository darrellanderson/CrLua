# gcloud app deploy app.yaml --project ti4-card-images
"""
"""

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import io
import os
import os.path
import webapp2

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
    return y + lineH

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
    return y + lineH

def wrapTextCenterHV(draw, font, text, x, y, maxWidth, fill):
    lines = []
    (spaceW, h) = font.getsize(' ')
    lineH = h + 10
    words = text.split(' ')
    text = ''
    lineWidth = 0
    for word in words:
        (w, h) = font.getsize(word)
        if lineWidth + w > maxWidth:
            lines.append(text)
            text = ''
            lineWidth = 0
        text += word + ' '
        lineWidth += w + spaceW
    lines.append(text)

    y = y - (len(lines) * lineH / 2)
    for line in lines:
        (lineWidth, h) = font.getsize(line)
        x2 = x - (lineWidth / 2)
        draw.text((x2, y), text, font=font, fill=fill)
        y += lineH
    return y + lineH

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
                y += lineH * 1.5
            if word.lower() == 'for:' or word.lower() == 'against:':
                indent = 20

    return y + lineH

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

class ActionCard(webapp2.RequestHandler):
    def get(self):
        img = getImage('ActionCard.jpg')
        draw = ImageDraw.Draw(img)

        font = getFont('HandelGothicDBold.otf', 44)
        color = (255, 232, 150, 255)
        text = self.request.get('title')
        text = text.upper()
        x = 85
        y1 = 92
        y2 = 72
        maxWidth = 400
        (w, h) = font.getsize(text)
        y = y1 if w <= maxWidth else y2
        wrapText(draw, font, text, x, y, maxWidth, color)

        font1 = getFont('MyriadProBold.ttf', 36)
        font2 = getFont('MyriadProSemibold.otf', 36)
        color = (255, 255, 255, 255)
        text = self.request.get('body')
        x = 60
        y = 200
        maxWidth = 480
        wrapTextBoldStart(draw, font1, font2, text, x, y, maxWidth, color)

        font = getFont('MyriadWebProItalic.ttf', 30)
        color = (255, 255, 255, 255)
        flavor = self.request.get('flavor')
        x = 270
        y = 575
        maxWidth = 425
        wrapTextCenter(draw, font, flavor, x, y, maxWidth, color)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(imageToJPEG(img))

class SecretObjectiveCard(webapp2.RequestHandler):
    def get(self):
        img = getImage('SecretObjective.jpg')
        draw = ImageDraw.Draw(img)

        font = getFont('HandelGothicDBold.otf', 44)
        color = (254, 196, 173, 255)
        text = self.request.get('title')
        text = text.upper()
        x = 250
        y1 = 35
        y2 = 15
        maxWidth = 400
        (w, h) = font.getsize(text)
        y = y1 if w <= maxWidth else y2
        wrapTextCenter(draw, font, text, x, y, maxWidth, color)

        x = 125
        y = 130
        w = 250
        h = 30
        color = (12, 12, 14, 255)
        draw.rectangle([(x, y), (x+w, y+h)], color)

        font = getFont('HandelGothicDBold.otf', 32)
        color = (255, 255, 255, 255)
        text = self.request.get('phase')
        text = text.upper()
        x = 250
        y = 130
        maxWidth = 400
        wrapTextCenter(draw, font, text, x, y, maxWidth, color)

        font = getFont('MyriadProSemibold.otf', 36)
        color = (255, 255, 255, 255)
        text = self.request.get('body')
        x = 250
        y = 375
        maxWidth = 450
        wrapTextCenterHV(draw, font, text, x, y, maxWidth, color)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(imageToJPEG(img))

class Stage1ObjectiveCard(webapp2.RequestHandler):
    def get(self):
        img = getImage('Stage1.jpg')
        draw = ImageDraw.Draw(img)

        font = getFont('HandelGothicDBold.otf', 44)
        color = (249, 249, 169, 255)
        text = self.request.get('title')
        text = text.upper()
        x = 250
        y1 = 35
        y2 = 15
        maxWidth = 400
        (w, h) = font.getsize(text)
        y = y1 if w <= maxWidth else y2
        wrapTextCenter(draw, font, text, x, y, maxWidth, color)

        font = getFont('MyriadProSemibold.otf', 36)
        color = (255, 255, 255, 255)
        text = self.request.get('body')
        x = 250
        y = 375
        maxWidth = 450
        wrapTextCenterHV(draw, font, text, x, y, maxWidth, color)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(imageToJPEG(img))

class Stage2ObjectiveCard(webapp2.RequestHandler):
    def get(self):
        img = getImage('Stage2.jpg')
        draw = ImageDraw.Draw(img)

        font = getFont('HandelGothicDBold.otf', 44)
        color = (173, 239, 254, 255)
        text = self.request.get('title')
        text = text.upper()
        x = 250
        y1 = 35
        y2 = 15
        maxWidth = 400
        (w, h) = font.getsize(text)
        y = y1 if w <= maxWidth else y2
        wrapTextCenter(draw, font, text, x, y, maxWidth, color)

        font = getFont('MyriadProSemibold.otf', 36)
        color = (255, 255, 255, 255)
        text = self.request.get('body')
        x = 250
        y = 375
        maxWidth = 450
        wrapTextCenterHV(draw, font, text, x, y, maxWidth, color)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(imageToJPEG(img))

class AgendaCard(webapp2.RequestHandler):
    def get(self):
        img = getImage('Agenda.jpg')
        draw = ImageDraw.Draw(img)

        font = getFont('HandelGothicDBold.otf', 44)
        color = (255, 255, 255, 255)
        text = self.request.get('title')
        text = text.upper()
        x = 250
        y1 = 35
        y2 = 15
        maxWidth = 400
        (w, h) = font.getsize(text)
        y = y1 if w <= maxWidth else y2
        wrapTextCenter(draw, font, text, x, y, maxWidth, color)

        x = 200
        y = 160
        w = 100
        h = 30
        color = (12, 12, 14, 255)
        draw.rectangle([(x, y), (x+w, y+h)], color)

        font = getFont('MyriadProBold.ttf', 30)
        color = (255, 255, 0, 255)
        text = self.request.get('type')
        text = text.upper()
        x = 250
        y = 165
        maxWidth = 400
        wrapTextCenter(draw, font, text, x, y, maxWidth, color)

        font1 = getFont('MyriadProBold.ttf', 30)
        font2 = getFont('MyriadProSemibold.otf', 30)
        color = (0, 0, 0, 255)
        text = self.request.get('body')
        text = 'Elect player\nFor: bar baz.\nMore.'
        text = 'Other thing\nFor: bar baz text goes here make it long to wrap.\nMore.'
        y = 220
        maxWidth = 480
        if 'Elect ' in text:
            for line in text.split('\n'):
                x = 250
                if line.startswith('Elect '):
                    y = wrapTextCenter(draw, font1, line, x, y, maxWidth, color)
                else:
                    y = wrapTextCenter(draw, font2, line, x, y, maxWidth, color)
                y += 20
        else:
            x = 60
            for line in text.split('\n'):
                if line.startswith('For:') or line.startswith('Against:'):
                    y = wrapTextBoldStart(draw, font1, font2, line, x, y, maxWidth, color)
                else:
                    y = wrapText(draw, font2, line, x, y, maxWidth, color)
                    y =y
                y += 20

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(imageToJPEG(img))

app = webapp2.WSGIApplication([
    ('/img', ActionCard),
    ('/action', ActionCard),
    ('/secret', SecretObjectiveCard),
    ('/stage1', Stage1ObjectiveCard),
    ('/stage2', Stage2ObjectiveCard),
    ('/agenda', AgendaCard),
], debug=True)
