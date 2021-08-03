import time
import datetime

from discord.ext.commands.cog import _cog_special_method

game = None
days = 0
curDay = 0
lastMessage = 0
categories = []
runs = []
scores = [12.50, 50.00, 37.50]
personalBests = dict()
winners = [[],[],[]]

class Category:
    def __init__(self, n, t, p=0.0) -> None:
        self.name = n
        self.type = t
        self.points = p

    def __str__(self) -> str:
        return self.name + " (" + self.type + "): "


class Run:
    def __init__(self, comp, cat, t, l) -> None:
        self.competitor = comp
        self.category = cat
        self.time: time.strptime = t
        self.link = l

    def getTime(self):
        t = ""
        if(int(self.time.tm_hour) > 0):
            t = str(self.time.tm_hour) + ":"
        t +=  str(self.time.tm_min) + ":" 
        if(int(self.time.tm_sec) < 10):
            t += "0"
        t += str(self.time.tm_sec)
        return t

    def __str__(self) -> str:
        t = self.getTime()
        return self.competitor + " (" + self.category + "): " + t + " (" + self.link + ")"

    def __gt__(self, run2):
        result = None
        try: 
            result = self.time > run2
        except: 
            result = self.time > run2.time
        return result


#data format: gameName;days;mainCatName;subCat1;subCat2;...; ;MiscCat1;MiscCat2;...
def init(data):
    try: 
        values = data.strip().split(';') #split data at semicolons
        #set primary fields
        newGame = values[0] 
        newDays = int(values[1])
        newCategories = []
        newCategories.append(Category(values[2], "Main"))
        #helper vars
        catType = "Sub"
        #set sub and misc. categories
        for i in range(3, len(values)): 
            if(values[i] == " "):
                catType = "Misc"
            else: 
                newCategories.append(Category(values[i], catType))
    except: 
        return "Invalid input, format: \"game name;number of days;main category;sub-category 1;sub-category 2; ... ; ;misc-category 1; ...\""
    # If input valid, then and only then set global variables
    global game
    game = newGame
    global days
    days = newDays
    global curDay
    curDay = 0
    global lastMessage
    x = datetime.datetime.now()
    lastMessage = int(x.strftime("%d"))
    global categories
    categories = newCategories
    global runs
    runs = []
    global personalBests
    personalBests.clear()
    global winners
    winners = [[],[],[]]
    setScores()
    # clear file
    initFile()
    return "Initalized new game, \"" + game + ",\" with " + str(len(categories)) + " phase 2 categories."


def info() -> str:
    global game, days
    return game + " will be speedrunned and phase 2 will last for a total of " + str(days) + " days."


def setScores(): 
    points = 6
    for cat in categories:
        personalBests[cat.name] = dict()
        if(cat.type == "Sub"):
            points += 4
        elif(cat.type == "Misc"):
            points += 3
    for cat in categories:
        if(cat.type == "Main"): 
            cat.points = float(6 / points * 50)
        elif(cat.type == "Sub"):
            cat.points = float(4 / points * 50)
        elif(cat.type == "Misc"):
            cat.points = float(3 / points * 50)


def getScores():
    announce = ""
    for phase in range(1, 4): #1,2,3
        announce += ("Phase " + str(phase) + ": " + "\n")
        if(phase == 2):
            for cat in categories:
                announce += ("     " + str(cat) + "\n")
                announce += ("          1st: " + format(float(cat.points),".2f") + "\n")
                announce += ("          2nd: " + format(float(cat.points)/2,".2f") + "\n")
                announce += ("          3rd: " + format(float(cat.points)/4,".2f") + "\n")
        else: 
            announce += ("     1st: " + format(float(scores[phase-1]),".2f") + "\n")
            announce += ("     2nd: " + format(float(scores[phase-1])/2,".2f") + "\n")
            announce += ("     3rd: " + format(float(scores[phase-1])/4,".2f") + "\n")
    return announce
            

# data format: name cat time link
def submitRun(data):
    try: 
        values = data.split(';') #split data at space
        #tests 
        good = False
        for cat in categories:
            if cat.name == values[1]:
                good = True
        if(not good):
            return "ERROR: Invalid Category"
        timeFormat = getTimeFormat(values[2])
        if(timeFormat == "ERROR"):
            return "ERROR: Invalid Time"
        #generate runs
        runTime = time.strptime(values[2],timeFormat)
        r = Run(values[0], values[1], runTime, values[3])
        addRun(r)
        announce = str(r) + " (#" + str(len(runs)) + ")"
        #check if personal best
        placeable = True
        if(values[0] in personalBests[values[1]]):
            if(personalBests[values[1]][values[0]] > runTime):
                personalBests[values[1]][values[0]] = runTime
                announce += " - **New Personal Best**"
            else: 
                placeable = False
        else:
            personalBests[values[1]][values[0]] = runTime
        #check if a top 3 time
        if(placeable):
            s = {k: v for k, v in sorted(personalBests[values[1]].items(), key=lambda item: item[1], reverse=False)}
            places = [" - **1st Place!**"," - **2nd Place!**"," - **3rd Place!**"]
            place = 1
            for name in s:
                if(name == values[0]):
                    announce += places[place-1]
                    break
                place += 1
                if(place == 4):
                    break
        return announce
    except:
        return "ERROR: Invalid input"


#time as string in HH:MM:SS or MM:SS format
def getTimeFormat(t):
    timeFormat = "%H:%M:%S"
    countColons = 0
    for c in t:
        if(c == ":"):
            countColons += 1
    if(countColons > 2):
        return "ERROR"
    if(countColons == 1):
        timeFormat = "%M:%S"
    return timeFormat


def tryDailyMessage():
    x = datetime.datetime.now()
    day = int(x.strftime("%d"))
    global lastMessage
    if(int(day) > int(lastMessage) or (day == 1 and lastMessage >= 28)): #not same day as last message, check for start of new month
        lastMessage = day
        hour = int(time.localtime(time.time())[3])
        if(int(hour) >= 19): #past 7pm
            return ""
        else: 
            return "Will not send the daily message until after 7PM."
    return "Already sent a message today."


def doDailyMessage():
    global curDay
    global days
    global lastMessage
    canSend = tryDailyMessage()
    if(canSend == ""):
        if(curDay < days):
            curDay += 1
            # update txt file
            f = open("data.txt", "r")
            lines = f.readlines()
            lines[1] = str(curDay) + "," + str(lastMessage) + "\n"
            f.close()
            f = open("data.txt", "w")
            f.writelines(lines)
            f.close()
            return ""
        else: 
            return "Phase 2 has already ended: day " + str(curDay) + " out of " + str(days)
    return canSend


def p2DailyAnnouncement():
    global game, curDay, days
    plural = "day"
    if(curDay > 1):
        plural = "days"
    announce = "Phase 2 Concluded"
    if(curDay == days):
        announce = "**END OF PHASE 2:**\n"
    else:
        announce = "**" + game + " Phase 2 Standings after " + str(curDay) + " " + plural + " (" + str(24*curDay) + " hours):**\n"
    announce += getRuns()
    return announce


def updateDayNumber(newDayStr):
    newDay = 0
    try: 
        newDay = int(newDayStr)
    except: 
        return "Error: Not a number."
    global days
    if(newDay >= 0 and newDay <= days):
        global curDay 
        curDay = newDay
        # update txt file
        f = open("data.txt", "r")
        lines = f.readlines()
        lines[1] = str(curDay) + "," + str(lastMessage) + "\n"
        f.close()
        f = open("data.txt", "w")
        f.writelines(lines)
        f.close()
        return "Changed day number to " + str(curDay)
    else: 
        return "Error: Invalid day number."
        


def convertTime(time):
    t = ""
    if(int(time.tm_hour) > 0):
        t = str(time.tm_hour) + ":"
    t +=  str(time.tm_min) + ":" 
    if(int(time.tm_sec) < 10):
        t += "0"
    t += str(time.tm_sec)
    return t


def getRuns(category = "all"):
    if(len(runs) == 0):
        return "No runs have been sumbitted."
    announce = ""
    for cat in categories:
        if(category == "all" or cat.name == category):
            announce += str(cat) + "\n"
            s = {k: v for k, v in sorted(personalBests[cat.name].items(), key=lambda item: item[1], reverse=False)}
            place = 1
            for run in s:
                print(personalBests[cat.name])
                announce += "     " + str(place) + ". " + str(run) + " - " + str(convertTime(personalBests[cat.name][run])) + "\n"
                place += 1
            if(place == 1):
                announce += "     *No runs*\n"
    if(announce == ""):
        return "Error: Invalid category"
    return announce
        

#data format: phase#;[1st];[2nd];[3rd]
def setWinners(data):
    values = data.split(';') #split data at semicolons
    if(len(values) > 4): #may only enter 
        return "Invalid input, format: \"phase number (1 or 3);first place;second place;third place"
    if(int(values[0]) == 1 or int(values[0]) == 3):
        array = int(values[0])-1
        for i in range(0,len(values)-1):
            addWinner(array, values[i+1], i+1)
        return "Winners of phase " + str(values[0]) + " updated."
    else: 
        return "Invalid phase number"


def addPoints(updatedScores, name, points):
    if(name in updatedScores):
        updatedScores[name] += points
    else: 
        updatedScores[name] = points
    # print(name + " earned " + str(points) + " for a total of " + str(updatedScores[name]))


def calcScores():
    updatedScores = dict()
    #phase 1
    if(winners[0] != [] and winners[0] != ["","",""]):
        #calculate points
        for i in range(0,3):  
            addPoints(updatedScores, winners[0][i], scores[0] / (2**i))
    #phase 2
    global curDay, days
    if(runs != []):
        if(int(curDay) >= int(days)):
            calcp2Scores(updatedScores)
    #phase 3
    if(winners[2] != [] and winners[2] != ["","",""]):
        #calculate points
        for i in range(0,3):  
            addPoints(updatedScores, winners[2][i], scores[2] / (2**i))
    return updatedScores


def calcp2Scores(updatedScores):
    for cat in categories:
        s = {k: v for k, v in sorted(personalBests[cat.name].items(), key=lambda item: item[1], reverse=False)}
        place = 1
        for name in s:
            addPoints(updatedScores, name, float(cat.points) / 2**(place-1))
            place += 1
            if(place == 4):
                break


def printScores(prefix):
    updatedScores = calcScores()
    if(len(updatedScores) > 0):
        s1 = {k: v for k, v in sorted(updatedScores.items(), key=lambda item: item[1], reverse=True)}
        announce = prefix + " Scores:\n"
        place = 1
        for name in s1:
            announce += str(place) + ". " + name + " - " + format(updatedScores[name],".2f") +"\n"
            place += 1
        return announce
    return "No one currently has any points."
            

def initFile():
    global game, curDay, days
    f = open("data.txt", "w")
    f.truncate() #remove existing content
    f.write(game+"\n" + str(curDay)+","+str(lastMessage)+"\n" + str(days)+"\n")
    toWrite = ""
    for i in range(0,3,2): #index 0 and 2
        for j in range(0,3):
            try: 
                toWrite += winners[i][j]
            except:
                pass
            toWrite += "\n"
    f.write(toWrite)
    toWrite = ""
    for cat in categories:
        toWrite += cat.name + "," + cat.type + "," + str(cat.points) + ";"
    f.write(toWrite + "\n")
    toWrite = ""
    for r in runs: 
        toWrite += r.competitor + "," + r.category + "," + str(r.time) + "," + r.link + "\n"
    f.write(toWrite)
    f.close()


def addRun(r):
    runs.append(r)
    f = open("data.txt", "a")
    f.write(r.competitor + ";" + r.category + ";" + r.getTime() + ";" + r.link + "\n")
    f.close()


def addWinner(phase, name, place):
    if(len(winners[phase]) < 3):
        winners[phase].append(name)
    else: 
        winners[phase][place-1] = name 
    f = open("data.txt", "r")
    lines = f.readlines()
    lineToChange = 2 + place
    if(phase == 2):
        lineToChange += 3
    lines[lineToChange] = name + "\n"
    f.close()
    f = open("data.txt", "w")
    f.writelines(lines)
    f.close()


def updatePBs():
    for run in runs:
        if(run.competitor in personalBests[run.category]):
            if(personalBests[run.category][run.competitor] > run.time):
                personalBests[run.category][run.competitor] = run.time
        else: 
            personalBests[run.category][run.competitor] = run.time


def editRun(user, runId, field, newValue):
    try: 
        if(int(runId) < 1 or int(runId) > len(runs)):
            return "ERROR: Invalid id"
    except: 
        return "ERROR: Invalid id"
    index = int(runId) - 1
    if(user != runs[index].competitor and user != "Moderator"):
        return "ERROR: Cannot edit someone else's run!"
    if(user == "Moderator" and (field == "0" or field == "competitor")):
        runs[index].competitor = newValue
    elif(field == "1" or field == "category"):
        runs[index].category = newValue
    elif(field == "2" or field == "time"):
        timeFormat = getTimeFormat(newValue)
        if(timeFormat == "ERROR"):
            return "ERROR: Invalid Time"
        runs[index].time = time.strptime(newValue,timeFormat)
    elif(field == "3" or field == "link"):
        runs[index].link = newValue
    else: 
        return "ERROR: Invalid Field"
    f = open("data.txt", "r")
    lines = f.readlines()
    lineToChange = int(runId) + 9
    lines[lineToChange] = runs[index].competitor + ";" + runs[index].category + ";" + str(runs[index].getTime()) + ";" + runs[index].link + "\n"
    f.close()
    f = open("data.txt", "w")
    f.writelines(lines)
    f.close()
    global personalBests
    for cat in categories:
        personalBests[cat.name].clear()
    updatePBs()
    return "Run " + str(runId) + " updated: " + str(runs[index])


def getRun(runId):
    if(len(runs) == 0):
        return "No runs have been sumbitted."
    try: 
        if(int(runId) < 0 or int(runId) > int(len(runs))):
            return "ERROR: Invalid id"
    except: 
        return "ERROR: Invalid id"
    announce = ""
    if(runId == 0):
        for i in range(0,len(runs)): 
            announce += str(i+1) + ". " + str(runs[i]) + "\n"
    else:
        index = int(runId) - 1
        announce = "Run #" + str(runId) + ": " + str(runs[index])
    return announce


# Read data from txt file:
try: 
    f = open("data.txt", "r")
    lines = f.readlines()
    if(len(lines) >= 10):
        #add global vars
        game = lines[0].strip() #remove newline
        dailyM = lines[1].strip().split(",")
        print(dailyM)
        curDay = int(dailyM[0])      #day number
        lastMessage = int(dailyM[1]) #last day daily message sent
        days = int(lines[2].strip())
        # add phase 1 and 3 winners
        winnersCounter = 3
        for i in range(0,3,2): #index 0 and 2
            winners.append([])
            for j in range(0,3):
                if(lines[winnersCounter] != ""):
                    winners[i].append(lines[winnersCounter].strip())
                winnersCounter += 1
        # add game categories
        cats = lines[9].strip().split(";") #get each category
        cats.pop() #remove empty string at end
        for c in cats: 
            categoryData = c.split(",") #get each element of category
            categories.append(Category(categoryData[0],categoryData[1],categoryData[2]))
            personalBests[categoryData[0]] = dict()
        # add runs
        for l in range(10,len(lines)): #for the remaining lines
            runData = lines[l].split(";")
            timeFormat = getTimeFormat(runData[2])
            runs.append(Run(runData[0],runData[1],time.strptime(runData[2],timeFormat),runData[3].strip()))
        updatePBs()
    f.close()
except:
    print("No data to read from")

        




# init("Super Bomberman;6;Any%;100%; ;No-power-up%")
# info()
# getScores()
# setWinners("1;Brent;Adam;Harrison")
# print(printScores("End of Phase 1"))
# print("-----")
# print(submitRun("Adam Any% 1:42:33 http://"))
# # print(getRuns())
# # print("-----")
# print(submitRun("Harrison Any% 50:33 http://"))
# # print(getRuns())
# # print("-----")
# print(submitRun("Adam Any% 39:33 http://"))
# # print(getRuns())
# # print("-----")
# print(submitRun("Harrison Any% 51:33 http://"))
# # print(getRuns())
# # print("-----")
# print(submitRun("Harrison Any% 29:33 http://"))
# print(getRuns())
# print("-----")
# print(printScores("End of Phase 2"))
# print("-----")
# setWinners("3;Harrison;Adam;Alan")
# print(printScores("Final"))


print(game)
print(curDay)
print(lastMessage)
print(days)
print(winners)
print(runs)
print(personalBests)
print(getRuns())
print("-----")
print(printScores("Finals"))
print(getScores())
print(getRun(3))
print(printScores("Finals"))