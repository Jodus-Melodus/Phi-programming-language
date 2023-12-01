import json
import sys
import re
import main, time
import customtkinter as ctk
from customtkinter import filedialog
import os
import keyboard

class TerminalRedirect:
    def __init__(self, textWidget:ctk.CTkTextbox) -> None:
        self.widget = textWidget

    def write(self, message) -> None:
        self.widget.configure(state='normal')
        self.widget.insert('end', message)
        self.widget.yview_moveto(1)
        self.widget.configure(state='disabled')

    def readline(self, prompt="") -> str:
        self.widget.insert('end', prompt)
        self.widget.mark_set("input_start", "end-1c")
        self.widget.mark_set("input_end", "end-1c + 1l")
        line = self.widget.get("input_start", "input_end")
        self.widget.delete("input_start", "input_end")
        return line

class Dropdown:
    def __init__(self, master, width:int, height:int, items:list, command, itempadx:int, itempady:int, bg_color:str):
        self.master = master
        self.width = width
        self.height = height
        self.items = items
        self.command = command
        self.itempadx = itempadx
        self.itempady = itempady
        self.itemFont = ctk.CTkFont(family='Fira Code', size=12, weight='normal')
        self.bg_color = bg_color

        self.ismapped = False
        self.currentSelectedIndex = 0

        self.frame = ctk.CTkFrame(self.master, width=self.width, height=self.height, bg_color=self.bg_color)

    def winfo_ismapped(self) -> bool:
        return self.ismapped
    
    def update(self) -> None:
        for child in self.frame.winfo_children():
            child.destroy()

    def place(self, x, y) -> None:
        self.update()
        for i, item in enumerate(self.items):
            btn = ctk.CTkButton(self.frame, text=item, command=lambda item=item: self.command(str(item)), font=self.itemFont, height=14, anchor='w', fg_color='#262626' if self.currentSelectedIndex == i else'#333333', hover_color='#262626')
            btn.pack(fill='both', expand=True, padx=self.itempadx, pady=self.itempady)
        self.frame.place(x=x, y=y)
        self.ismapped = True

    def place_forget(self) -> None:
        self.update()
        self.frame.place_forget()
        self.ismapped = False

class Dialog:
    def __init__(self, master, title:str, message:str, x:int, y:int) -> None:
        self.master = master
        self.title = title
        self.message = message
        self.x = x
        self.y = y
        self.width = 500
        self.height = 250

        self.dialog = ctk.CTkFrame(self.master, width=self.width, height=self.height, corner_radius=5)
        title = ctk.CTkLabel(self.dialog, anchor='nw', text=self.title, font=ctk.CTkFont(family='Fira Code', size=14))
        msg = ctk.CTkTextbox(self.dialog, font=ctk.CTkFont(family='Fira Code', size=12))
        close = ctk.CTkButton(self.dialog, text='Close', command=self._close, font=ctk.CTkFont(family='Fira Code', size=12))

        msg.insert('0.0', self.message)
        msg.configure(wrap='word')

        title.pack(fill='both', anchor='nw', padx=10, pady=10)
        msg.pack(fill='both', expand=True, anchor='s', padx=10, pady=10)
        close.pack(expand=True, anchor='se', padx=10, pady=10)

        self.dialog.place(x=self.x-self.width//4, y=self.y-self.height//2)

    def _close(self) -> None:
        self.dialog.destroy()

class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title('phIDE')
        self.state('zoomed')
        self.textBoxFont = ctk.CTkFont(family='Courier New', size=16, weight='bold')
        self.buttonFont = ctk.CTkFont(family='Fira Code', size=12, weight='normal')
        self.screenRatio = 0.65
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.padx = 5
        self.pady = 5
        self.currentPath = ''
        self.currentLanguage = ''
        self.openEditors = {}
        self.tabNamesPaths = {}
        self.line = 1
        self.column = 1
        self.clipboard = ''
        self.menuOpen = False
        self.rightMenuOpen = False
        self.saved = False
        self.code = ''
        self.centerx = self.width // 2
        self.centery = self.height // 2
        self.cursors = []

        self.loadLanguageSyntax()
        # Frames
        self.leftPanel = ctk.CTkFrame(self, width=200)
        self.rightPanel = ctk.CTkFrame(self, width=200)
        self.bottomPanel = ctk.CTkFrame(self)
        self.centerPanel = ctk.CTkFrame(self)
        self.findAndReplacePanel = ctk.CTkFrame(self.rightPanel)
        self.gotoPanel = ctk.CTkFrame(self.rightPanel)
        self.menuBar = ctk.CTkFrame(self, height=20)
        # Tabviews
        self.centerTabview = ctk.CTkTabview(self.centerPanel, self.width*self.screenRatio, height=self.height*self.screenRatio)
        self.bottomTabview = ctk.CTkTabview(self.bottomPanel, width=self.width*self.screenRatio)
        self.consoleTab = self.bottomTabview.add('Console')
        # Textboxes
        self.console = ctk.CTkTextbox(self.consoleTab, font=self.textBoxFont, state='disabled')
        # Buttons
        self.clearConsoleButton = ctk.CTkButton(self.consoleTab, text='Clear', command=self.clearConsole, width=50, height=20, font=self.buttonFont)
        self.findAndReplaceButton = ctk.CTkButton(self.findAndReplacePanel, command=self.findAndReplaceClick, text='Find & Replace', font=self.buttonFont)
        self.gotoButton = ctk.CTkButton(self.gotoPanel, command=self.gotoClick, text='Go to', font=self.buttonFont)
        # Menu Buttons & Popups
        self.fileMenu = ctk.CTkButton(self.menuBar, text='File', height=20, width=50, command=self.fileMenuClick, font=self.buttonFont)
        self.editMenu = ctk.CTkButton(self.menuBar, text='Edit', height=20, width=50, command=self.editMenuClick, font=self.buttonFont)
        self.runMenu = ctk.CTkButton(self.menuBar, text='Run', height=20, width=50, command=self.runMenuClick, font=self.buttonFont)
        self.fileMenuPopup = ctk.CTkSegmentedButton(self, values=['New File', 'Open File', 'Save File', 'Close File'], command=self.processMenuShortcuts, height=20, font=self.buttonFont)
        self.editMenuPopup = ctk.CTkSegmentedButton(self, values=['Undo', 'Redo', 'Copy', 'Paste', 'Replace', 'Comment'], command=self.processMenuShortcuts, height=20, font=self.buttonFont)
        self.runMenuPopup = ctk.CTkSegmentedButton(self, values=['Run'], command=self.processMenuShortcuts, height=20, font=self.buttonFont)
        self.rightClickPopup = Dropdown(self, 300, 100, ['New File', 'Open File', 'Save File', 'Close File', 'Run', 'Undo', 'Redo', 'Copy', 'Paste', 'Replace', 'Comment'], self.processMenuShortcuts, 2, 2, '#ff00ff')
        # Labels
        self.statusbar = ctk.CTkLabel(self, text='', height=20, font=self.buttonFont)
        # Entries
        self.find = ctk.CTkEntry(self.findAndReplacePanel, placeholder_text='Find', font=self.buttonFont)
        self.replace = ctk.CTkEntry(self.findAndReplacePanel, placeholder_text='Replace', font=self.buttonFont)
        self.gotoEntry = ctk.CTkEntry(self.gotoPanel, placeholder_text='Go to line', font=self.buttonFont)
        # ComboBox
        self.currentLanguageCombo = ctk.CTkOptionMenu(self.menuBar, height=20, values=[x for x in self.languageSyntaxPatterns], font=self.buttonFont)
        # Other
        sys.stdin = TerminalRedirect(self.console)
        sys.stdout = TerminalRedirect(self.console)
        sys.stderr = TerminalRedirect(self.console)

        self.menuBar.pack(padx=self.padx, pady=self.pady, anchor='w')
        self.currentLanguageCombo.pack(padx=self.padx, pady=self.pady, expand=True, anchor='e', side='right')
        self.fileMenu.pack(padx=self.padx, pady=self.pady, expand=True, anchor='w', side='left')
        self.editMenu.pack(padx=self.padx, pady=self.pady, expand=True, anchor='w', side='left')
        self.runMenu.pack(padx=self.padx, pady=self.pady, expand=True, anchor='w', side='left')

        self.gotoButton.pack(padx=self.padx, pady=self.pady, side='bottom')
        self.gotoEntry.pack(padx=self.padx, pady=self.pady, side='top', expand=True)
        self.find.pack(padx=self.padx, pady=self.pady, side='top', expand=True)
        self.replace.pack(padx=self.padx, pady=self.pady, expand=True)
        self.findAndReplaceButton.pack(padx=self.padx, pady=self.pady, side='bottom')
        self.statusbar.pack(padx=self.padx, pady=self.pady, side=ctk.BOTTOM, anchor='se', expand=True)
        self.clearConsoleButton.pack(padx=self.padx, pady=self.pady, side=ctk.RIGHT, anchor='n')
        self.console.pack(padx=self.padx, pady=self.pady, fill='both', expand=True)

        self.rightPanel.pack(padx=self.padx, pady=self.pady, fill='both', expand=True, side=ctk.RIGHT, anchor='e')
        self.leftPanel.pack(padx=self.padx, pady=self.pady, fill='both', expand=True, side=ctk.LEFT, anchor='w')
        self.centerPanel.pack(padx=self.padx, pady=self.pady, fill='both', expand=True)
        self.bottomPanel.pack(padx=self.padx, pady=self.pady, fill='both', expand=True, anchor='s')

        self.centerTabview.pack(padx=self.padx, pady=self.pady, expand=True, fill='both')
        self.bottomTabview.pack(padx=self.padx, pady=self.pady, expand=True, fill='both')

        # Bindings
# Single Character Sequence
        self.bind('<F1>', self.showHelp)
        self.bind('<F5>', self.run)
        self.bind('<Return>', self.enterCommands)
        self.bind('<Escape>', self.escapeKeyPress)
        self.bind('<(>', self.autoParenthesis)
        self.bind('<[>', self.autoBracket)
        self.bind('<{>', self.autoBrace)
        self.bind('<">', self.autoDoubleQuote)
        self.bind("<'>", self.autoApostrophe)
        self.bind('<KeyPress>', self.keyPressUpdate)
# Double Character Sequence
        self.bind('<Control-F4>', self.closeFile)
        self.bind('<Control-BackSpace>', self.backspaceEntireWord)
        self.bind('<Control-space>', self.intelliSenseTrigger)
        self.bind('<Control-Tab>', self.nextTab)
        self.bind('<Control-/>', self.commentLine)
        self.bind('<Control-;>', self.showSnippets)
        self.bind('<Control-]>', self.indent)
        self.bind('<Control-[>', self.dedent)
        self.bind('<Control-k>', self.openFolder)
        self.bind('<Control-o>', self.openFiles)
        self.bind('<Control-s>', self.saveFile)
        self.bind('<Control-n>', self.newFile)
        self.bind('<Control-c>', self.copy)
        self.bind('<Control-v>', self.paste)
        self.bind('<Control-z>', self.undo)
        self.bind('<Control-h>', self.toggleFindAndReplaceMenu)
        self.bind('<Control-g>', self.toggleGoToMenu)
# Triple Character Sequence
        self.bind('<Control-Shift-z>', self.redo)
        self.bind('<Control-Shift-Tab>', self.prevTab)
# Mouse Click
        self.bind('<Button-1>', self.mouseClickUpdate)
        self.bind('<ButtonRelease-1>', self.highlightSelected)
        self.bind('<Button-2>', self.multiCursor)
        self.bind('<Control-Button-1>', self.multiCursor)
        self.bind('<Button-3>', self.rightClickMenuClick)

        self.mainloop()

    def showHelp(self, e=None) -> None:
        helpWindow = ctk.CTkToplevel()
        helpWindow.title('phIDE - Help')
        helpText = ctk.CTkTextbox(helpWindow, font=self.textBoxFont)
        helpText.pack(expand=True, fill='both')
        text = """        F1 -                    Show this menu
        F5 -                    Run current file
        Enter -                 Select first intellisense word
        Ctrl + Backspace -      Deletes entire word
        Ctrl + Space -          Manually open intellisense
        Ctrl + ; -              Show Snippet menu
        Ctrl + / -              Comment current line
        Ctrl + K -              Open folder
        Ctrl + O -              Open file
        Ctrl + S -              Save current file
        Ctrl + N -              Creates a new file
        Ctrl + F4 -             Close current tab
        Ctrl + C -              Copy selected text
        Ctrl + V -              Paste last copied word
        Ctrl + Z -              Undo action
        Ctrl + Shift + Z -      Redo action
        Ctrl + H -              Open and closes the find and replace panel
        Ctrl + G -              Open and closes the go to panel
        Ctrl + [ -              Dedent line or selected text
        Ctrl + ] -              Indent line or selected text
        Ctrl + Tab -            Next tab
        Ctrl + Shift + Tab -    Previous Tab
        Ctrl + Left Click -     Add/remove cursor
        Middle Click -          Add/remove cursor
        Esc -                   Hide intelliSense
        """
        helpText.insert('0.0', text)
        helpText.configure(wrap='none', state='disabled')

    @property
    def currentTab(self) -> ctk.CTkTextbox:
        tabName = self.centerTabview.get()
        if tabName != '':
            return self.openEditors[tabName]
        
    def clearConsole(self) -> None:
        self.console.configure(state='normal')
        self.console.delete('0.0', 'end')
        self.console.configure(state='disabled')

    def addTab(self, path:str) -> None:
        self.currentPath = path
        self.currentLanguage = '.' + path.split('/')[-1].split('.')[-1]
        self.currentLanguageCombo.set(self.currentLanguage)

        tabName = path.split('/')[-1]
        if tabName not in self.centerTabview._tab_dict:
            tab = self.centerTabview.add(tabName)

            editor = ctk.CTkTextbox(tab, font=self.textBoxFont)
            editor.configure(tabs=40)
            editor.configure(wrap='none')
            
            for tag in self.languageSyntaxPatterns[self.currentLanguage]:
                editor.tag_config(tag, foreground=self.languageSyntaxPatterns[self.currentLanguage][tag][0])
            editor.tag_config('error', background='#990000')
            editor.tag_config('similar', background='#595959')
            editor.tag_config('cursor', background='#444444')

            editor.pack(expand=True, fill='both')

            self.intelliSenseBox = Dropdown(editor, 300, 100, [], self.intelliSenseClickInsert, 2, 2, '#ff00ff')
            self.snippetMenu = Dropdown(editor, 300, 100, [], self.insertSnippet, 2, 2, '#3366ff')
            editor.bind('<Tab>', self.intelliSenseTabKeyPress)
            editor.bind('<Up>', self.intelliSenseUpKeyPress)
            editor.bind('<Down>', self.intelliSenseDownKeyPress)
            editor.bind('<KeyPress>', self.editorPress)

            self.openEditors[tabName] = editor
            self.tabNamesPaths[tabName] = path

            length = 0
            with open(path, 'r') as f:
                for line in f.readlines():
                    length += 1
                    editor.insert('end', line)
                    self.updateSyntax(line, length)
            
            self.code = editor.get('0.0', 'end')
            self.loadSnippets()
        else:
            Dialog(self, 'Error', 'Cannot open two files with the same name.', self.centerx, self.centery)

# Updates
    def incrementIndex(self, cursor:str) -> str:
        line, char = cursor.split('.')
        
        return f'{line}.{str(int(char) + 1)}'
    
    def decrementIndex(self, cursor:str) -> str:
        line, char = cursor.split('.')

        if char == '0':
            return str(int(line) - 1) + '.lineend'
        
        return f'{line}.{str(int(char) - 1)}'
    
    def updateMultiCursors(self, e) -> None:
        editor = self.currentTab
        if editor:

            editor.tag_remove('cursor', '0.0', 'end')

            for cursor in self.cursors:
                editor.tag_add('cursor', cursor, cursor + '+1c')

            new = []
            for index in self.cursors:
                if index != editor.index('insert'):
                    key = e.keysym.lower()
                    if key not in ['control_l', 'control_r', 'shift_L', 'shift_r', 'alt_L', 'alt_r']:
                        if key == 'left':
                            new.append(self.decrementIndex(index))
                        elif key == 'right':
                            new.append(self.incrementIndex(index))
                        elif key == 'backspace':
                            editor.delete(index + '-1c', index)
                            new.append(self.decrementIndex(index))
                        elif key == 'space':
                            editor.insert(index, ' ')
                            new.append(self.incrementIndex(index))
                        else:
                            editor.insert(index, key)
                            new.append(self.incrementIndex(index))

            self.cursors = new
            print(self.cursors)

    def keyPressUpdate(self, e=None) -> None:
        self.currentLanguage = self.currentLanguageCombo.get()
        editor = self.currentTab
        if editor:
            self.line, self.column = editor.index('insert').split('.')
            self.statusbar.configure(text=f'Ln {self.line}, Col {self.column}')

        self.updateMultiCursors(e)
        self.updateSyntax()

        if hasattr(self, 'intelliSenseBox'):
            if self.intelliSenseBox.winfo_ismapped():
                self.intelliSenseTrigger
        if hasattr(self, 'snippetMenu'):
            if self.snippetMenu.winfo_ismapped():
                self.showSnippets

        editor = self.currentTab
        if editor:
            currentCode = editor.get('0.0', 'end')
            if currentCode != self.code:
                name = self.centerTabview.get()
                self.title(name if self.saved else name + '*')

    def editorPress(self, e=None) -> None:
        self.saved = False

        editor = self.currentTab
        if editor:
            currentCode = editor.get('0.0', 'end')
            if currentCode != self.code:
                name = self.centerTabview.get()
                self.title(name if self.saved else name + '*')

    def mouseClickUpdate(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.tag_remove('similar', '0.0', 'end')

    def highlightSelected(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            text = editor.get('0.0', 'end').split('\n')
            if editor.tag_ranges('sel'):
                w = editor.get(ctk.SEL_FIRST, ctk.SEL_LAST)
                word = re.escape(w)
                pattern = f'({word})'
                for ln, line in enumerate(text):
                    matches = [(match.start(), match.end()) for match in re.finditer(pattern, line)]
                    for start, end in matches:
                        editor.tag_add('similar', f'{ln+1}.{start}', f'{ln+1}.{end}')
                        editor.tag_remove('error', f'{ln}.0', f'{ln}.end')

    def enterCommands(self, e=None) -> None:
        self.intelliSenseEnterInsert()
        self.enterSnippets()

# Snippets
    def enterSnippets(self) -> None:
        if self.snippetMenu.winfo_ismapped():
            if len(self.snippetMenu.items) > 0:
                editor = self.currentTab
                if editor:
                    snippetName = self.snippetMenu.items[self.snippetMenu.currentSelectedIndex]
                    startLine, startColumn = map(int, editor.search(r'\s', 'insert-1c', backwards=True, regexp=True).split('.'))
                    if startColumn == 0:
                        startLine += 1
                        startPos = f'{startLine}.{startColumn}'
                    else:
                        startPos = f'{startLine}.{startColumn + 1}'
                    editor.delete(startPos, 'insert')
                    editor.insert(startPos, self.snippets[snippetName] + ' ')
                    editor.focus_set()
                    self.snippetMenu.place_forget()
                    self.updateSyntax()

    def insertSnippet(self, snippetName:str) -> None:
        editor = self.currentTab
        if editor:
            snippet = self.snippetMenu.items[snippetName]
            startLine, startColumn = map(int, editor.search(r'\s', 'insert-1c', backwards=True, regexp=True).split('.'))
            if startColumn == 0:
                startLine += 1
                startPos = f'{startLine}.{startColumn}'
            else:
                startPos = f'{startLine}.{startColumn + 1}'
            editor.delete(startPos, 'insert')
            editor.insert(startPos, snippet + ' ')
            editor.focus_set()
            self.snippetMenu.place_forget()
            self.updateSyntax()

    def showSnippets(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            self.snippetMenu.place_forget()
            x, y, _, _ = editor.bbox(editor.index('insert'))
            currentIndex = editor.index('insert')
            wordStart = editor.search(r'(\s|\.|,|\)|\(|\[|\]|\{|\}|\t)', currentIndex, backwards=True, regexp=True)
            word = editor.get(wordStart, currentIndex).strip(' \n\t\r')

            if word:
                words = []
                for w in self.snippets:
                    if w.startswith(word):
                        words.append(w)
                if len(words) > 0:
                    if self.intelliSenseBox.winfo_ismapped():
                        self.intelliSenseBox.place_forget()
                    self.snippetMenu.items = words
                    self.snippetMenu.place(x=x, y=y+30)
            else:
                if self.intelliSenseBox.winfo_ismapped():
                    self.intelliSenseBox.place_forget()
                self.snippetMenu.items = self.snippets
                self.snippetMenu.place(x=x, y=y+30)

    def loadSnippets(self) -> None:
        with open(f'snippets/{self.currentLanguage[1:]}.json') as f:
            self.snippets = json.load(f)

# Syntax
    def loadLanguageSyntax(self) -> None:
        with open('syntax.json', 'r') as f:
            self.languageSyntaxPatterns = json.load(f)

    def updateSyntax(self, line:str=None, lnIndex:int=None) -> None:
        editor = self.currentTab
        if editor:
            for tag in self.languageSyntaxPatterns[self.currentLanguage]:
                pattern = self.languageSyntaxPatterns[self.currentLanguage][tag][1]
                if not line:
                    currLineEnd = editor.index('insert lineend')
                    currLine = currLineEnd.split('.')[0]
                    editor.tag_remove(tag, f'{currLine}.0', f'{currLine}.end')
                    text = editor.get(f"{currLineEnd.split('.')[0]}.0", currLineEnd)
                else:
                    text = line
                    currLine = lnIndex
                matches = [(match.start(), match.end()) for match in re.finditer(pattern, text)]
                for start, end in matches:
                    editor.tag_add(tag, f'{currLine}.{start}', f'{currLine}.{end}')
                    editor.tag_remove('error', f'{currLine}.0', f'{currLine}.end')

# IntelliSense

    def intelliSenseTabKeyPress(self, e=None) -> None:
        if self.intelliSenseBox.winfo_ismapped():
            keyboard.press('Backspace')
            self.intelliSenseBox.currentSelectedIndex += 1
            if self.intelliSenseBox.currentSelectedIndex >= len(self.intelliSenseBox.items):
                self.intelliSenseBox.currentSelectedIndex = 0
            self.intelliSenseTrigger()
        elif self.snippetMenu.winfo_ismapped():
            keyboard.press('Backspace')
            self.snippetMenu.currentSelectedIndex += 1
            if self.snippetMenu.currentSelectedIndex >= len(self.snippetMenu.items):
                self.snippetMenu.currentSelectedIndex = 0
            self.showSnippets()

    def intelliSenseUpKeyPress(self, e=None) -> None:
        if self.intelliSenseBox.winfo_ismapped():
            keyboard.press('Up')
            self.intelliSenseBox.currentSelectedIndex -= 1
            if self.intelliSenseBox.currentSelectedIndex < 0:
                self.intelliSenseBox.currentSelectedIndex = len(self.intelliSenseBox.items) - 1
            self.intelliSenseTrigger()
        elif self.snippetMenu.winfo_ismapped():
            keyboard.press('Up')
            self.snippetMenu.currentSelectedIndex -= 1
            if self.snippetMenu.currentSelectedIndex < 0:
                self.snippetMenu.currentSelectedIndex = len(self.snippetMenu.items) - 1
            self.showSnippets()

    def intelliSenseDownKeyPress(self, e=None) -> None:
        if self.intelliSenseBox.winfo_ismapped():
            self.intelliSenseBox.currentSelectedIndex += 1
            if self.intelliSenseBox.currentSelectedIndex >= len(self.intelliSenseBox.items):
                self.intelliSenseBox.currentSelectedIndex = 0
            self.intelliSenseTrigger()
        elif self.snippetMenu.winfo_ismapped():
            self.snippetMenu.currentSelectedIndex += 1
            if self.snippetMenu.currentSelectedIndex >= len(self.snippetMenu.items):
                self.snippetMenu.currentSelectedIndex = 0
            self.showSnippets()
            
    def intelliSenseTrigger(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            self.intelliSenseBox.place_forget()
            intelliSenseWords = self.languageSyntaxPatterns[self.currentLanguage]['keywords'][2]
            x, y, _, _ = editor.bbox(editor.index('insert'))
            currentIndex = editor.index('insert')
            wordStart = editor.search(r'(\s|\.|,|\)|\(|\[|\]|\{|\}|\t)', currentIndex, backwards=True, regexp=True)
            word = editor.get(wordStart, currentIndex).strip(' \n\t\r')
            if word:
                words = []
                for w in intelliSenseWords:
                    if w.startswith(word):
                        words.append(w)
                if len(words) > 0:
                    if self.snippetMenu.winfo_ismapped():
                        self.snippetMenu.place_forget()
                    self.intelliSenseBox.items = words
                    self.intelliSenseBox.place(x=x, y=y+30)
            else:
                if self.snippetMenu.winfo_ismapped():
                    self.snippetMenu.place_forget()
                self.intelliSenseBox.items = intelliSenseWords
                self.intelliSenseBox.place(x=x, y=y+30)

    def intelliSenseEnterInsert(self, e=None) -> None:
        if self.intelliSenseBox.winfo_ismapped():
            if len(self.intelliSenseBox.items) > 0:
                editor = self.currentTab
                if editor:           
                    keyboard.press('Backspace')
                    selectedWord = self.intelliSenseBox.items[self.intelliSenseBox.currentSelectedIndex]
                    startLine, startColumn = map(int, editor.search(r'\s', 'insert-1c', backwards=True, regexp=True).split('.'))
                    if startColumn == 0:
                        startLine += 1
                        startPos = f'{startLine}.{startColumn}'
                    else:
                        startPos = f'{startLine}.{startColumn + 1}'
                    editor.delete(startPos, 'insert')
                    editor.insert(startPos, selectedWord + ' ')
                    editor.focus_set()
                    self.intelliSenseBox.place_forget()
                    self.updateSyntax()

    def intelliSenseClickInsert(self, selected) -> None:
        editor = self.currentTab
        if editor:
            startLine, startColumn = map(int, editor.search(r'\s', 'insert-1c', backwards=True, regexp=True).split('.'))
            if startColumn == 0:
                startLine += 1
                startPos = f'{startLine}.{startColumn}'
            else:
                startPos = f'{startLine}.{startColumn + 1}'
            editor.delete(startPos, 'insert')
            editor.insert(startPos, selected + ' ')
            editor.focus_set()
            self.intelliSenseBox.place_forget()
            self.updateSyntax()

# Menu Bar
    def rightClickMenuClick(self, e=None) -> None:
        if self.rightMenuOpen:
            self.rightClickPopup.place_forget()
            self.rightMenuOpen = False
        else:
            self.rightClickPopup.place(x=e.x, y=e.y)
            self.rightMenuOpen = True

    def fileMenuClick(self) -> None:
        self.fileMenuPopup.set('')
        if self.menuOpen:
            self.fileMenuPopup.place_forget()
            self.editMenuPopup.place_forget()
            self.runMenuPopup.place_forget()
            self.menuOpen = False
        else:
            self.fileMenuPopup.place(x=self.fileMenu.winfo_x()+5, y=self.fileMenu.winfo_y()+30)
            self.menuOpen = True

    def editMenuClick(self) -> None:
        self.editMenuPopup.set('')
        if self.menuOpen:
            self.fileMenuPopup.place_forget()
            self.editMenuPopup.place_forget()
            self.runMenuPopup.place_forget()
            self.menuOpen = False
        else:
            self.editMenuPopup.place(x=self.editMenu.winfo_x()+5, y=self.editMenu.winfo_y()+30)
            self.menuOpen = True

    def runMenuClick(self) -> None:
        self.runMenuPopup.set('')
        if self.menuOpen:
            self.fileMenuPopup.place_forget()
            self.editMenuPopup.place_forget()
            self.runMenuPopup.place_forget()
            self.menuOpen = False
        else:
            self.runMenuPopup.place(x=self.runMenu.winfo_x()+5, y=self.runMenu.winfo_y()+30)
            self.menuOpen = True

    def processMenuShortcuts(self, name:str) -> None:
        self.fileMenuPopup.place_forget()
        self.editMenuPopup.place_forget()
        self.runMenuPopup.place_forget()
        self.rightClickPopup.place_forget()
        match name:
            case 'New File':
                self.newFile()
            case 'Open File':
                self.openFiles()
            case 'Save File':
                self.saveFile()
            case 'Close File':
                self.closeFile()
            case 'Undo':
                self.undo()
            case 'Redo':
                self.redo()
            case 'Copy':
                self.copy()
            case 'Paste':
                self.paste()
            case 'Replace':
                self.toggleFindAndReplaceMenu()
            case 'Comment':
                self.commentLine()
            case 'Run':
                self.run()

# Side Menus
    def toggleGoToMenu(self, e=None) -> None:
        if self.gotoPanel.winfo_ismapped():
            self.gotoPanel.pack_forget()
            editor = self.currentTab
            if editor:
                editor.focus_set()
        else:
            self.gotoPanel.pack()
            self.find.focus_set()

    def toggleFindAndReplaceMenu(self, e=None) -> None:
        if self.findAndReplacePanel.winfo_ismapped():
            self.findAndReplacePanel.pack_forget()
            editor = self.currentTab
            if editor:
                editor.focus_set()
        else:
            self.findAndReplacePanel.pack()
            self.find.focus_set()
        
    def gotoClick(self) -> None:
        editor = self.currentTab
        if editor:
            lineNumber = int(self.gotoEntry.get())
            index = f'{lineNumber}.0'
            editor.see(index)

    def findAndReplaceClick(self) -> None:
        find = self.find.get()
        replace = self.replace.get()
        editor = self.currentTab
        new = []
        if editor:
            text = editor.get('0.0', 'end').split('\n')
            for line in text:
                words = re.findall(r'\S+|\s', line)
                for word in words:
                    w = word
                    if find in word:
                        new.append(w.replace(find, replace))
                    else:
                        new.append(word)
                new.append('\n')
            editor.delete('0.0', 'end')
            editor.insert('0.0', ''.join(new))

# Shortcuts
    def multiCursor(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            index = editor.index('current')
            if index in self.cursors:
                self.cursors.remove(index)
            else:
                self.cursors.append(editor.index('current'))

    def indent(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            selected = editor.tag_ranges('sel')
            if selected:
                startPosition, endPosition = selected[0].string, selected[1].string
                startLine = int(startPosition.split('.')[0])
                endLine = int(endPosition.split('.')[0])
                while startLine != endLine:
                    editor.insert(f'{startLine}.0', '\t')
                    startLine += 1
            else:
                line = editor.index('insert').split('.')[0]
                editor.insert(f'{line}.0', '\t')

    def dedent(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            selected = editor.tag_ranges('sel')
            if selected:
                startPosition, endPosition = selected[0].string, selected[1].string
                startLine = int(startPosition.split('.')[0])
                endLine = int(endPosition.split('.')[0])
                while startLine != endLine:
                    curr = editor.get(str(startLine) + '.0', str(startLine) + '.1')
                    if curr == '\t':
                        editor.delete(str(startLine) + '.0', str(startLine) + '.1')
                    startLine += 1
            else:
                line = editor.index('insert').split('.')[0]
                curr = editor.get(line+'.0', line+'.1')
                if curr == '\t':
                    editor.delete(line + '.0', line+'.1')

    def escapeKeyPress(self, e=None) -> None:
        if hasattr(self, 'intelliSenseBox'):
            if self.intelliSenseBox.winfo_ismapped():
                self.intelliSenseBox.place_forget
        if hasattr(self, 'snippetMenu'):
            if self.snippetMenu.winfo_ismapped():
                self.snippetMenu.place_forget

    def prevTab(self, e=None) -> None:
        tabs = list(self.centerTabview._tab_dict.keys())
        newTabIndex = self.centerTabview.index(self.centerTabview.get()) - 1
        if newTabIndex >= 0:
            newTabName = tabs[newTabIndex]
            self.centerTabview.set(newTabName)

    def nextTab(self, e=None) -> None:
        tabs = list(self.centerTabview._tab_dict.keys())
        newTabIndex = self.centerTabview.index(self.centerTabview.get()) + 1
        if newTabIndex < len(tabs):
            newTabName = tabs[newTabIndex]
            self.centerTabview.set(newTabName)

    def autoApostrophe(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.insert('insert', "'")
            editor.mark_set('insert', 'insert -1c')

    def autoDoubleQuote(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.insert('insert', '"')
            editor.mark_set('insert', 'insert -1c')

    def autoParenthesis(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.insert('insert', ')')
            editor.mark_set('insert', 'insert -1c')

    def autoBracket(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.insert('insert', ']')
            editor.mark_set('insert', 'insert -1c')

    def autoBrace(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.insert('insert', '}')
            editor.mark_set('insert', 'insert -1c')

    def closeFile(self, e=None) -> None:
        self.saveFile()
        tabName = self.centerTabview.get()
        self.centerTabview.delete(tabName)
        self.title('phIDE')

    def openFolder(self, e=None) -> None:
        dirPath = filedialog.askdirectory(title='Select a folder')
        files = [os.path.join(root, file) for root, dirs, files in os.walk(dirPath) for file in files]
        if files:
            for file in files:
                self.addTab(file.replace('\\', '/'))

    def openFiles(self, e=None) -> None:
        filePath = filedialog.askopenfilenames(title='Select a file', filetypes=[('Phi File', '*.phi'), ('All Files', '*.*')])
        if filePath:
            for file in filePath:
                self.addTab(file)

    def backspaceEntireWord(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            currentIndex = editor.index('insert')
            wordStart = editor.search(r'\s', currentIndex, backwards=True, regexp=True)
            editor.delete(wordStart, currentIndex)

    def run(self, e=None) -> None:
        self.saveFile()
        if self.currentPath != '':
            with open(self.currentPath, 'r') as f:
                sourceCode = ''.join(f.readlines())
            start = time.time()
            self.console['state'] = 'normal'
            error = main.run(sourceCode)
            if error:
                editor = self.currentTab
                if editor:
                    line = error.line
                    editor.tag_add('error', f'{line}.0', f'{line}.end')
                    text = editor.get(f'{line}.0', f'{line}.end')
                    print(text)
                    print(error)
            self.console['state'] = 'disabled'
            end = time.time()
            print(f"\nProcess finished in {end - start} seconds.")
            print('-'*60+'\n')

    def commentLine(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            cursor_position = editor.index('insert')
            line_number = cursor_position.split('.')[0]
            startPosition = f"{line_number}.0"
            endPosition = f'{line_number}.2'
            commented = editor.get(startPosition, endPosition)
            if commented == '# ':
                editor.delete(startPosition, endPosition)
            else:
                editor.insert(startPosition, '# ')
            editor.tag_remove('sel', '0.0', 'end')
            self.updateSyntax()

    def saveFile(self, e=None) -> None:
        if not self.currentPath:
            self.currentPath = filedialog.asksaveasfilename(title='Select a file', filetypes=[('Phi File', '*.phi'), ('All Files', '*.*')])

        editor = self.currentTab
        if editor:
            text = editor.get('0.0', 'end')
            with open(self.currentPath, 'w') as f:
                f.write(text)
        self.saved = True

    def newFile(self, e=None) -> None:
        self.currentPath = filedialog.asksaveasfilename(title='Select a file', filetypes=[('Phi File', '*.phi'), ('All Files', '*.*')])
        with open(self.currentPath, 'w') as f:
            f.write('')
        self.addTab(self.currentPath)

    def copy(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            self.clipboard = editor.selection_get()

    def paste(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.insert('insert', self.clipboard)

    def undo(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.edit_undo()
    
    def redo(self, e=None) -> None:
        editor = self.currentTab
        if editor:
            editor.edit_redo()

if __name__ == '__main__':
    app = App()
