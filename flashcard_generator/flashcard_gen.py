from tkinter import *
import random
import time
root = Tk()
root.title("Japanese Flashcard Generator")
#root.iconbitmap("japanese_flag.ico")
root.geometry("550x500")

#replace word or letters with ones you would like to learn
hiragana_letters = [
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

#keep adding to list as more term lists are added. will automate this in the future through OCR scans
overall_vocab_list = [hiragana_letters, words_section_1]
current_index = 0
current_vocab_list = overall_vocab_list[current_index]
count = len(overall_vocab_list[current_index])
# print("Initial count is", count)
# print("Initial index is", current_index)
def clear_label():
    hint_label.config(text="")
    answer_label.config(text="")

def next():
    global random_word
    global hinter
    global hint_count
    random_word = random.randint(0, count -1)
    foreign_word.config(text=current_vocab_list[random_word][0])
    hint_label.config(text="")
    answer_label.config(text="")
    entry.delete(0, END)
    hinter = ""
    hint_count = 0
    print("New word index is", random_word)
    #native_word.config(text=words_and_letters[random_word][1])
    #root.after(2000, clear_label)
def answer():
    if entry.get() == current_vocab_list[random_word][1]:
        answer_label.config(text=f"Correct! {current_vocab_list[random_word][1]} is {current_vocab_list[random_word][0]}")
    else:
        answer_label.config(text=f"Incorrect! {entry.get().lower()} is not {current_vocab_list[random_word][0]}")
    
hinter = ""
hint_count = 0
def hint():
    global hinter
    global hint_count
    if hint_count <= len(current_vocab_list[random_word][1]):
        hinter = hinter + current_vocab_list[random_word][1][hint_count]
        hint_label.config(text=hinter)
        hint_count += 1
    # print("Current hint count with hint button is", hint_count)
    # print("Current hint string with hint button is", hinter)


vocab_list_labels = ['Hiragana Characters',
    'Section 1 Vocab']#,
    # 'Numbers',
    # 'Time']

def next_vocab_list():
    global current_index
    global current_vocab_list
    global hinter
    global hint_count
    global count
    if current_index < len(vocab_list_labels)-1:
        current_index += 1
    else:
        current_index = 0
    current_vocab_list = overall_vocab_list[current_index]
    random_word = random.randint(0, count -1)
    foreign_word.config(text=current_vocab_list[random_word][0])
    hint_label.config(text="")
    answer_label.config(text="")
    vocab_list_label.config(text=vocab_list_labels[current_index])

    entry.delete(0, END)
    hinter = ""
    hint_count = 0
    count = len(overall_vocab_list[current_index])
    # print("Hint string after changing vocab is", hinter)
    # print("Hint count after changing vocab is", hint_count)
    # print("Vocabl list length after changing vocab is", count)
    # print("Current vocab list index after changing vocab is", current_index)
    next()
    
    
    
    
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
answer_button.grid(row=0, column=0, padx=10)

next_button = Button(button_frame, text="Next", command = next)
next_button.grid(row=0, column=1)

hint_button = Button(button_frame, text="Hint", command = hint)
hint_button.grid(row=0, column=2, padx=10)

next_vocab_button = Button(button_frame, text="Next Vocab List", command = next_vocab_list)
next_vocab_button.grid(row=1, column= 0, padx=20)

show_vocab_button = Button(button_frame, text = "Show Vocab List")
show_vocab_button.grid(row=1, column=2, padx = 20)

vocab_list_label = Label(root, text="", font=("Helvetica", 20))

hint_label = Label(root, text=vocab_list_labels[current_index], font=("Helvetica", 20))
hint_label.pack(pady=5)

# troubleshoot_label = Label(root, text = print(str(hint_count)), font=("Helvetica", 20))
# troubleshoot_label.pack(pady=5)

next()
root.mainloop()