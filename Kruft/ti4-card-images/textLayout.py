#!/usr/bin/env python
# -*- coding: latin-1 -*-
# @author Darrell

import os
import re

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageColor

_visualizeMargins = False

# -----------------------------------------------------------------------------

class FontData:
    def __init__(self, fontName, fontSize, color):
        self._type = 'FontData'
        dir = os.path.dirname(__file__)
        static = os.path.join(dir, 'static')
        self._fontName = fontName
        self._fontSize = fontSize
        self._color = color
        self._file = os.path.join(static, fontName)
        self._font = ImageFont.truetype(self._file, self._fontSize)
        self._dy = 0

    def clone(self):
        return FontData(self._fontName, self._fontSize, self._color)

    def applyOffset(self, otherFontData):
        assert otherFontData._type == 'FontData'
        _, h1 = otherFontData._font.getsize('X')
        _, h2 = self._font.getsize('X')
        self._dy = h1 - h2
        print('applyOffset.dy: me=' + str(otherFontData._fontSize) + ' them=' + str(otherFontData._fontSize) + ' d=' + str(self._dy))

    def setOffset(self, dy):
        self._dy = dy

    def width(self, text):
        (w, _) = self._font.getsize(text)
        return w

    def getColor(self):
        return self._color

    def draw(self, text, imageDraw, x, y, lineH):
        imageDraw.text((x, y + self._dy), text, font=self._font, fill=self._color)

    def resize(self, delta):
        self._fontSize += delta
        result = True
        if self._fontSize <= 0:
            self._fontSize = 1
            result = False
        self._font = ImageFont.truetype(self._file, self._fontSize)
        return result

# -----------------------------------------------------------------------------

class WordData:
    def __init__(self, word, fontData):
        assert fontData._type == 'FontData'
        self._type = 'WordData'
        self._word = word
        self._fontData = fontData
        self._width = fontData.width(word)

    def __str__(self):
        return '{' + self._word + '}'

    def resetFont(self, fontData):
        assert fontData._type == 'FontData'
        self._fontData = fontData
        self._width = fontData.width(self._word)

    def width(self):
        return self._width

    def draw(self, imageDraw, x, y, lineH):
        #word = self._word.encode('utf-8')
        #print('TEXT_LAYOUT: ADDING "' + word + '", width=' + str(self._width) + ' at x=' + str(x))
        if not self._word.isspace():
            self._fontData.draw(self._word, imageDraw, x, y, lineH)

    def getWord(self):
        return self._word

    def isSpace(self):
        return self._word == ' '

    def isNewline(self):
        return self._word == '\n'

# -----------------------------------------------------------------------------

class LineData:
    def __init__(self, indent):
        self._type = 'LineData'
        self._indent = indent
        self._words = []

    def __str__(self):
        words = []
        for word in self._words:
            words.append(str(word))
        return ', '.join(words)

    def width(self):
        result = self._indent
        for wordData in self._words:
            result += wordData.width()
        return result

    def draw(self, imageDraw, x, y, lineH):
        x += self._indent
        prevWord = False
        gather = ''
        for word in self._words:
            if word._word == '\n':
                prevWord._fontData.draw(gather, imageDraw, x, y, lineH)
                x += prevWord._fontData.width(gather)
                prevWord = False
                gather = ''
            elif (not prevWord) or (word._fontData == prevWord._fontData):
                prevWord = word
                gather += word._word
            else:
                prevWord._fontData.draw(gather, imageDraw, x, y, lineH)
                x += prevWord._fontData.width(gather)
                prevWord = word
                gather = word._word
        if prevWord:
            prevWord._fontData.draw(gather, imageDraw, x, y, lineH)
            x += prevWord._fontData.width(gather)

    def addWord(self, wordData):
        assert wordData._type == 'WordData'
        self._words.append(wordData)

    def getWords(self):
        return self._words

    def isEmpty(self):
        if len(self._words) == 0:
            return True
        if len(self._words) == 1 and self._words[0].getWord() == '\n':
            return True
        return False

# -----------------------------------------------------------------------------

class Parse:
    @staticmethod
    def parseWordsAndPunctuation(line):
        r = re.compile(r'[\w]+|[^\s\w]', re.UNICODE)
        result = []
        for line in line.split('\n'):  # split by and restore newlines
            for word in line.split():
                for item in r.findall(word):
                    result.append(item)  # words and punctuation as separate items
                result.append(' ')
            if len(result) > 0 and result[-1] == ' ':
                result.pop()  # remove last space
            result.append('\n')
        if len(result) > 0:
            result.pop()  # remove last return
        return result

class Format:
    @staticmethod
    def getLineData(parsedWords, fontData):
        assert fontData._type == 'FontData'
        lineData = LineData(0)
        for word in parsedWords:
            lineData.addWord(WordData(word, fontData))
        return lineData

    @staticmethod
    def applyBoldStart(lineData, boldFontData):
        assert lineData._type == 'LineData'
        assert boldFontData._type == 'FontData'
        bolding = True
        result = LineData(lineData._indent)
        for wordData in lineData.getWords():
            text = wordData.getWord()
            if text == ':' and result.isEmpty():
                # As a hack, if the first character is ':' drop it and stop bolding.
                bolding = False
            elif bolding:
                result.addWord(WordData(text, boldFontData))
                if text == ':' or text == '\n':
                    bolding = False
            else:
                result.addWord(wordData)
        return result

    @staticmethod
    def overrideMagicWords(lineData, wordSet, overrideFontData):
        assert lineData._type == 'LineData'
        assert overrideFontData._type == 'FontData'
        result = LineData(lineData._indent)
        boldNext = False
        for wordData in lineData.getWords():
            text = wordData.getWord()
            if boldNext or text in wordSet:
                result.addWord(WordData(text, overrideFontData))
                boldNext = False
            else:
                result.addWord(wordData)
        return result

    @staticmethod
    def fold(lineData, maxWidth, indent):
        assert(lineData._type == 'LineData')
        currentLine = LineData(0)
        result = [ currentLine ]

        # Make groups to prevent wrapping between word and punctuation.
        currentGroup = []
        wordDataGroups = [ currentGroup ]
        for wordData in lineData.getWords():
            text = wordData.getWord()
            if text.isspace() or text == '\n':
                wordDataGroups.append([ wordData ])
                currentGroup = []
                wordDataGroups.append(currentGroup)
            else:
                currentGroup.append(wordData)

        for wordDataGroup in wordDataGroups:
            width = 0
            isNewline = False
            for wordData in wordDataGroup:
                width += wordData.width()
                isNewline = isNewline or wordData.getWord() == '\n'

            # Always add the first word, even if it exceeds max width.
            overflow = currentLine.width() + width > maxWidth
            if isNewline:
                # Add to current, THEN start a new line.
                for wordData in wordDataGroup:
                    currentLine.addWord(wordData)
                currentLine = LineData(indent)
                result.append(currentLine)
            elif overflow and not currentLine.isEmpty():
                # Start a new line, add to next line.
                currentLine = LineData(indent)
                result.append(currentLine)
                for wordData in wordDataGroup:
                    currentLine.addWord(wordData)
            else:
                for wordData in wordDataGroup:
                    currentLine.addWord(wordData)

        # Remove spaces at the start or end of lines.
        for line in result:
            words = line.getWords()
            while len(words) > 0 and words[0].isSpace():
                words.pop(0)
            while len(words) > 0 and words[-1].isSpace():
                words.pop()

        return result

    @staticmethod
    def unfold(lineDataList):
        mergedLineData = LineData(0)
        for lineData in lineDataList:
            if not lineData.isEmpty():
                lastWord = False
                for wordData in lineData.getWords():
                    if not wordData.isNewline():
                        mergedLineData.addWord(wordData)
                        lastWord = wordData
                if lastWord:
                    space = WordData(' ', lastWord._fontData)
                    mergedLineData.addWord(space)
        return mergedLineData

# -----------------------------------------------------------------------------

class TextBlock:
    def __init__(self):
        self._type = 'TextBlock'
        self._text = ''
        self._centerH = False
        self._centerV = False
        self._alignBottom = False
        self._lineH = 0
        self._indent = 0
        self._bounds = (0, 0, 0, 0)
        self._newlineScale = 1
        self._font = False
        self._boldStartFont = False
        self._overrideWordSet = False
        self._overrideFont = False
        self._gradualShrink = False

    def setCenterH(self, value):
        self._centerH = value
        return self

    def setCenterV(self, value):
        self._centerV = value
        return self

    def setAlignBottom(self, value):
        self._alignBottom = value
        return self

    def setLineHeight(self, lineH):
        self._lineH = lineH
        return self

    def setIndent(self, indent):
        self._indent = indent
        return self

    def setBounds(self, l, t, r, b):
        self._bounds = (l, t, r, b)
        return self

    def setNewlineScale(self, value):
        self._newlineScale = value
        return self

    def setFont(self, fontData):
        assert fontData._type == 'FontData'
        self._font = fontData
        return self

    def setBoldStart(self, boldFontData):
        assert boldFontData._type == 'FontData'
        self._boldStartFont = boldFontData
        return self

    def setOverride(self, overrideWordSet, overrideFont):
        self._overrideWordSet = overrideWordSet
        self._overrideFont = overrideFont
        return self

    def setText(self, text):
        self._text = text
        return self

    def setGradualShrink(self, value):
        self._gradualShrink = value
        return self

    def draw(self, imageDraw):
        # If gradually shrinking text make a copy to mutate in place.
        localLineH = self._lineH
        if self._gradualShrink:
            self._font = self._font.clone()
            if self._boldStartFont:
                self._boldStartFont = self._boldStartFont.clone()
            if self._overrideFont:
                self._overrideFont = self._overrideFont.clone()

        # Parse text, apply fonts.
        text = Parse.parseWordsAndPunctuation(self._text)
        lineData = Format.getLineData(text, self._font)
        if self._boldStartFont:
            lineData = Format.applyBoldStart(lineData, self._boldStartFont)
        if self._overrideWordSet:
            lineData = Format.overrideMagicWords(lineData, self._overrideWordSet, self._overrideFont)

        # Fold into lines.
        (l, t, r, b) = self._bounds
        lineDataList = Format.fold(lineData, r - l, self._indent)

        # Draw.
        if _visualizeMargins:
            color = (255, 0, 0, 255)
            imageDraw.rectangle([(l, t), (r, b)], outline=color, width=2)

        h = len(lineDataList) * self._lineH
        y = t
        if self._centerV:
            y = ((t + b) / 2) - (h / 2)
        elif self._alignBottom:
            y = b - h

        while len(lineDataList) > 0:
            line = lineDataList.pop(0)
            if line.isEmpty():
                y += localLineH * (self._newlineScale - 1)
            else:
                x = l
                if self._centerH:
                    x = ((l + r) / 2) - (line.width() / 2)
                line.draw(imageDraw, x, y, localLineH)
                y += localLineH

            if self._gradualShrink:
                # Shrink.
                delta = min(-int(self._font._fontSize * 0.15), -1)
                if not self._font.resize(delta):
                    break
                if self._boldStartFont:
                    self._boldStartFont.resize(delta)
                if self._overrideFont:
                    self._overrideFont.resize(delta)
                localLineH = int(self._font._fontSize * 1.3)

                # Re-fold remaining text.
                if len(lineDataList) > 0:
                    lineData = Format.unfold(lineDataList)
                    for wordData in lineData.getWords():
                        wordData.resetFont(wordData._fontData)
                    lineDataList = Format.fold(lineData, r - l - self._indent, self._indent)
                    lineDataList[0]._indent = self._indent

        return y, h

    def drawGradient(self, image, fromColor, toColor):
        (l, t, r, b) = self._bounds

        # Get just the text on a transparent background.
        w, h = image.size
        sample = Image.new('RGBA', (w, h))
        draw = ImageDraw.Draw(sample)
        self.draw(draw)
        sample = sample.crop((l, t, r, b))
        w, h = sample.size

        # Create a gradient from black to white.  Image.linear_gradient not available on AppEngine. :(
        #gradient = Image.linear_gradient('L')
        gradient = Image.new('L', (100, 1))
        data = []
        for i in range(100):
            data.append(i * 255 / 100)
        gradient.putdata(data)
        gradient = gradient.resize((w, h))

        # Use it to make one from color to color.
        solid = Image.new('RGBA', (w, h), toColor)
        gradient2 = Image.new('RGBA', (w, h), fromColor)
        gradient2.paste(solid, (0, 0), gradient)

        # Paste transparent to white over the text.
        image.paste(gradient2, (l, t), sample)
