from tkinter import *
import random
import time
root = Tk()
root.title("Japanese Flashcard Generator")
#root.iconbitmap("japanese_flag.ico")
root.geometry("550x410")

#replace word or letters with ones you would like to learn
words_and_letters = [
    (("あ"), ("a")),
    (("い"), ("i")),
    (("う"), ("u")),
    (("え"), ("e")),
    (("お"), ("o")),
    (("か"), ("ka")),
    (("き"), ("ki")),
    (("く"), ("ku")),
    (("け"), ("ke")),
    (("こ"), ("ko")),
    (("さ"), ("sa")),
    (("し"), ("shi")),
    (("す"), ("su")),
    (("せ"), ("se")),
    (("そ"), ("so")),
    (("た"), ("ta")),
    (("ち"), ("chi")),
    (("つ"), ("tsu")),
    (("て"), ("te")),
    (("と"), ("to")),
    (("な"), ("na")),
    (("に"), ("ni")),
    (("ぬ"), ("nu")),
    (("ね"), ("ne")),
    (("の"), ("no")),
    (("は"), ("ha")),
    (("ひ"), ("hi")),
    (("ふ"), ("fu")),
    (("へ"), ("he")),
    (("ほ"), ("ho")),
    (("ま"), ("ma")),
    (("み"), ("mi")),
    (("む"), ("mu")),
    (("め"), ("me")),
    (("も"), ("mo")),
    (("や"), ("ya")),
    (("ゆ"), ("yu")),
    (("よ"), ("yo")),
    (("ら"), ("ra")),
    (("り"), ("ri")),
    (("る"), ("ru")),
    (("れ"), ("re")),
    (("ろ"), ("ro")),
    (("わ"), ("wa")),
    (("を"), ("wo")),
    (("ん"), ("n")),
    (("が"), ("ga")),
    (("ぎ"), ("gi")),
    (("ぐ"), ("gu")),
    (("げ"), ("ge")),
    (("ご"), ("go")),
    (("ざ"), ("za")),
    (("じ"), ("ji")),
    (("ず"), ("zu")),
    (("ぜ"), ("ze")),
    (("ぞ"), ("zo")),
    (("だ"), ("da")),
    (("ぢ"), ("ji")),
    (("づ"), ("zu")),
    (("で"), ("de")),
    (("ど"), ("do")),
    (("ば"), ("ba")),
    (("び"), ("bi")),
    (("ぶ"), ("bu")),
    (("べ"), ("be")),
    (("ぼ"), ("bo")),
]
#add a romanji label next time
words_section_1 = [
    (("あの"), ("um")),
    (("いま"), ("now")),
    (("えいご"), ("English")),
    (("ええ"),   ("yes")),
    (("がくせい"), ("student")),
    (("こうこう"), ("high school")),
    (("ごご"),     ("pm")),
    (("ごぜん"),  ("am")),
    (("せんこう"), ("major")),
    (("せんせい"), ("teacher")),
    (("そうです"), ("thats right")),
    #can make native entry a list of answers depending on word
    #will have it loop through when clicking the answer button in the future
    #make popup or label that shows whole list of vocab if desired
    (("そうですか"), ("i see")),
    (("だいがく"), ("college")),
    (("でんわ"), ("phone")),
    (("ともだち"), ("friend")),
    (("なまえ"),    ("name")),
    (("なん"),   ("what")),
    (("なに"),    ("what")),
    (("にほん"),   ("japan")),
    (("はい"),    ("yes")),
    (("はん"),   ("half")),
    (("ばんごう"), ("number")),
    (("りゅうがくせい"), ("internatアメリカ ional student")),
    (("わたし"),  ("I")),
    (("アメリカ"), ("USA")),
    (("イギリス"), ("Britain")),
    (("オーストラリア"), ("Australia")),
    (("かんこく"), ("Korea")),
    (("スウェーデン"), ("Swedan")),
    (("ちゅうごく"), ("China")),
    (("かがく"), ("Science")),
    (("アジアけんきゅう"), ("Asian studies")),
    (("けいざい"), ("Economics")),
    (("こくさいかんけえ"), ("International relations")),
    (('コンプューター'), ("computer")),
    (('じんるいがく'), ('anthropology')),
    (("せいじ"), ("politics")),
    (("ビジネス"), ("business")),
    (("ぶんがく"), ("literature")),
    (("れきし"), ('history')),
    (("しごと"), ("job")),
    (("いしゃ"), ("doctor")),
    (("かいしゃいん"), ("office worker")),
    (("こうこうせい"), ("high school students")),
    (("しゅふ"), ("housewife")),
    (("だいがくいんせい"), ("graduate student")),
    (("だいがくせい"), ("college student")),
    (("べんごし"), ('lawyer')),
    (("おかあさん"), ('mother')),
    (('おとうさん'), ('father')),
    (('おねえさん'), ('older sister')),
    (('おにいさん'), ('older brother')),
    (('いもうと'), ('younger sister')),
    (('おとうと'), ('younger brother'))
]

numbers = [
    (('いち'), ('one')),
    (('に'), ('two')),
    (('さん'), ('three')),
    (('よん'), ('four'))
]
hours = [

]
words_section_2 = [

]

count = len(words_and_letters)
def clear_label():
    hint_label.config(text="")
    answer_label.config(text="")

def next():
    global random_word
    random_word = random.randint(0, count -1)
    foreign_word.config(text=words_and_letters[random_word][0])
    hint_label.config(text="")
    answer_label.config(text="")
    entry.delete(0, END)
    
    #native_word.config(text=words_and_letters[random_word][1])
    #root.after(2000, clear_label)
def answer():
    if entry.get() == words_and_letters[random_word][1]:
        answer_label.config(text=f"Correct! {words_and_letters[random_word][1]} is {words_and_letters[random_word][0]}")
    else:
        answer_label.config(text=f"Incorrect! {entry.get().lower()} is not {words_and_letters[random_word][0]}")
    

def hint():
    hinter = ""
    hint_count = 0
    if hint_count <= len(words_and_letters[random_word][1]):
        hinter = hinter + words_and_letters[random_word][1][hint_count]
        hint_label.config(text=hinter)
        hint_count += 1

foreign_word = Label(root, text="", font=("Helvetica", 36))
foreign_word.pack(pady=20)

answer_label = Label(root, text="", font=("Helvetica", 20))
answer_label.pack(pady=20)

native_word = Label(root, text="")
native_word.pack(pady=20)

entry = Entry(root, font=("Helvetica", 18))
entry.pack(pady=20)

button_frame = Frame(root)
button_frame.pack(pady=20)

answer_button = Button(button_frame, text="Answer", command = answer)
answer_button.grid(row=0, column=0, padx=20)

next_button = Button(button_frame, text="Next", command = next)
next_button.grid(row=0, column=1)

hint_button = Button(button_frame, text="Hint", command = hint)
hint_button.grid(row=0, column=2, padx=20)

hint_label = Label(root, text="", font=("Helvetica", 20))
hint_label.pack(pady=5)

# troubleshoot_label = Label(root, text = print(str(hint_count)), font=("Helvetica", 20))
# troubleshoot_label.pack(pady=5)

next()
root.mainloop()