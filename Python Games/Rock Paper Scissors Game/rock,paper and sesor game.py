import pyttsx3
import speech_recognition as sr
import datetime
import random
import pyjokes
from requests import get




engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
print(voices[0].id)
engine.setProperty('voice',voices[0].id)
engine.setProperty('rate', 180)

def speak(audio):
   engine.say(audio)
   print(audio)
   engine.runAndWait()

def wishme():
   hour = int(datetime.datetime.now().hour)
   if hour>=0 and hour<12:
      speak("Good Morning")
      
   elif hour>12 and hour<18:
      speak("Good Afternoon!")
      
   elif hour>18 and hour<24:
      speak("Good Evening")

   else:
      speak("good evening")

def count():
   for i in range(3,0,-1):
      speak(i)

def game():
    import random
    t=0
    t1=0
    p0=[] 
    p10=[]
    total=[]
    speak(" 1. Rock")
    speak(" 2. Paper")
    speak(" 3. Sesor")
    speak("\n")
    while True:
        n=input("Enter your choice:  ")
        c=random.randint(1,3)
        i=0
    
    
#------------------ FUNCTION CREATION -------------------------------
        def rock():
            p=0
            p1=0
            pc=0
            if n.lower()=="rock":
                speak("Rock")
                i="1"
                if i=="1" and c== 1:
                    speak("player 1: Rock")
                    speak("player 2: Rock")
                    speak("Both Equals....")
                    print()
                
                
                if i=="1" and c== 2:
                    speak("player 1: Rock")
                    speak("player 2: paper")
                    speak("player 2 Wins....")
                    p1=p1+1
                    print("\n")
                if i=="1" and c== 3:
                    speak("player 1: Rock")
                    speak("player 2: Sesor")
                    speak("player 1 Wins....")
                    p=p+1
                    print("\n")
            
                p0.append(p)
                pc=pc+1
                total.append(pc)
                p10.append(p1)
        def paper():
            p=0
            p1=0
            pc=0
            if n.lower()=="paper": 
                i="2"
                if i=="2":
                    speak("Paper")
                if i=="2" and c== 2:
                    speak("player 1: paper")
                    speak("player 2: paper")
                    speak("Both Equlas....")
                    print()
                
                
                if i=="2" and c== 1:
                    speak("player 1: paper")
                    speak("player 2: Rock")
                    speak("player 1 Wins....")
                    p=p+1
                    print("\n")
                if i=="2" and c== 3:
                    speak("player 1: paper")
                    speak("player 2: Sesor")
                    speak("player 2 Wins....")
                    p1=p1+1
                    print("\n")
                pc=pc+1
                total.append(pc)
                p0.append(p)
                p10.append(p1)    
        def sesor():
            p=0
            p1=0
            pc=0
        
            if n.lower()=="sesor":
                i="3"
                if i=="3":
                    speak("Sesor")
                    if i=="3" and c== 3:
                        speak("player 1: sesor")
                        speak("player 2: sesor")
                        speak("Both Equals....")
                        print()
                    if i=="3" and c== 1:
                        speak("player 1: Sesor")
                        speak("player 2: Rock")
                        speak("player 2 Wins....")
                        p1=p1+1
                        print("\n")
                    if i=="3" and c== 2:
                        speak("player 1: Sesor")
                        speak("player 2: paper")
                        speak("player 1 Wins....")
                        p=p+1
                        print("\n")
                    pc=pc+1
                    total.append(pc)
                    p0.append(p)
                    p10.append(p1)

#----------------------- FUNCTION RECALL -------------------------
        print("\n")
        rock()
        paper()
        sesor()
        if n=="exit":
            break

#---------------FOR STATEMENTS -------------------------------------  
    you=0   
    for i in range(0,(len(total))):
        you=you+(total[i])
    for i in range(0,(len(p0))):
        t=t+(p0[i])
    
    print("Score Round player 1:",p0)
    for y in range(0,(len(p10))):
        t1=t1+(p10[y])

    print("Score Round player 2:",p10)

    print()
    speak("     Calculating Results.....    ")
    print("\n")

#------------------ STATEMENTS AND RESULTS ---------------------------
    if t==t1:
        speak("...............Match is Draw..............")
    elif t>t1:
        speak("    player 1 is Winner of the Match:  ")
        print("    player 1 is Winner by:  ",t)
        print("\n")
    else:
        speak("    player 2 is Winner of the Match:  ")
        print("    player 2 is Winner by:  ",t1)
        print("\n")

    
    
    print("  score of Player 1:  ",t)
    
    print("  score of Player 2:  ",t1)
    sui=you-(t+t1)
    
    print("  Draw Matches: ...   ",sui)
    
    print("  Total matches are:  ",you)
def takecommand():
   #it take microphone input from the user and return string output
 
   r = sr.Recognizer()
   with sr.Microphone() as source:
     print("listening...")
     r.pause_threshold = 1
     audio = r.listen(source)
    
   try:
      print("recognizing...")
      query = r.recognize_google(audio, language='en-in')
      print(f"user said: {query}\n")
      

      
   except Exception as e:
       print("say that again please...")
       return "none"
   return query


if __name__ == "__main__":
   wishme()
   count()
   speak("Go")
   game()
  