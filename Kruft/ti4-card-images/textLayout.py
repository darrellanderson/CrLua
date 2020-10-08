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
        file = os.path.join(static, fontName)
        self._font = ImageFont.truetype(file, fontSize)
        self._color = color
        self._dy = 0

    def applyOffset(self, otherFontData):
        assert otherFontData._type == 'FontData'
        _, h1 = otherFontData._font.getsize('X')
        _, h2 = self._font.getsize('X')
        self._dy = h1 - h2

    def width(self, text):
        (w, _) = self._font.getsize(text)
        return w

    def draw(self, text, imageDraw, x, y, lineH):
        imageDraw.text((x, y + self._dy), text, font=self._font, fill=self._color)

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

    def resetFont(fontData):
        assert fontData._type == 'FontData'
        self._fontData = fontData
        self._width = fontData.width(word)

    def width(self):
        return self._width

    def draw(self, imageDraw, x, y, lineH):
        self._fontData.draw(self._word, imageDraw, x, y, lineH)

    def getWord(self):
        return self._word

    def isSpace(self):
        return self._word == ' '

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
        for word in self._words:
            word.draw(imageDraw, x, y, lineH)
            x += word.width()

    def addWord(self, wordData):
        assert wordData._type == 'WordData'
        self._words.append(wordData)

    def getWords(self):
        return self._words

    def isEmpty(self):
        return len(self._words) == 0

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
            if len(result) > 0:
                result.pop()  # remove last space
            result.append('\n')
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
        for wordData in lineData.getWords():
            # Always add the first word, even if it exceeds max width.
            overflow = currentLine.width() + wordData.width() > maxWidth
            isNewline = wordData.getWord() == '\n'
            if isNewline:
                # Add to current, THEN start a new line.
                currentLine.addWord(wordData)
                currentLine = LineData(indent)
                result.append(currentLine)
            elif overflow and not currentLine.isEmpty():
                # Start a new line, add to next line.
                currentLine = LineData(indent)
                result.append(currentLine)
                currentLine.addWord(wordData)
            else:
                currentLine.addWord(wordData)

        # Remove spaces at the start or end of lines.
        for line in result:
            words = line.getWords()
            while len(words) > 0 and words[0].isSpace():
                words.pop(0)
            while len(words) > 0 and words[-1].isSpace():
                words.pop()

        return result

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

    def draw(self, imageDraw):
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
        for line in lineDataList:
            if line.isEmpty():
                y += self._lineH + self._newlineScale
                continue
            x = l
            if self._centerH:
                x = ((l + r) / 2) - (line.width() / 2)
            line.draw(imageDraw, x, y, self._lineH)
            words = line.getWords()
            if len(words) >0 and words[-1].getWord() == '\n':
                y += self._lineH * self._newlineScale
            else:
                y += self._lineH

        return y, h