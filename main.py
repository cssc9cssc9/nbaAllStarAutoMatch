# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from adbutils import adb, AdbDevice
import numpy as np
import aircv
import json
import random
from PyQt6 import QtCore, QtGui, QtWidgets

class allstarWorker(QtCore.QThread):
    randomClick = False
    randomTime = False
    connectPort = ""
    startMode = 0
    startTimes = 0
    device = None

    isStart = QtCore.pyqtSignal()
    isProgress = QtCore.pyqtSignal(str)
    isFinish = QtCore.pyqtSignal()
    isError = QtCore.pyqtSignal()

    emitLog = QtCore.pyqtSignal(str)
    emitMoney = QtCore.pyqtSignal(str)
    emitStone = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def setVariable(self, connectPort:str, startTimes:int, randomTime: bool, randomClick:bool):
        self.startTimes = startTimes
        self.connectPort = connectPort
        self.randomClick = randomClick
        self.randomTime = randomTime
        
    
    def run(self):
        self.isStart.emit()
        QtCore.QThread.sleep(1)
        try:
            self.emitLog.emit("===== 初始化 =====")
            self.__registerADBDeivce()
            QtCore.QThread.sleep(1)
            self.emitLog.emit("初始化完成")
            self.emitLog.emit(f"隨機點擊: {'開啟' if self.randomClick else '關閉'}")
            self.emitLog.emit(f"隨機時間: {'開啟' if self.randomTime else '關閉'}")
            QtCore.QThread.sleep(1)
            self.emitLog.emit("===== 開始掛機 =====")

            startMatchImg = aircv.cv2.cvtColor(aircv.imread("./img/startMatchButton.png"), aircv.cv2.COLOR_BGR2RGB)
            matchingImg = aircv.cv2.cvtColor(aircv.imread("./img/matchStillGoOn.png"), aircv.cv2.COLOR_BGR2RGB)
            matchFinishImg = aircv.cv2.cvtColor(aircv.imread("./img/matchFinish.png"), aircv.cv2.COLOR_BGR2RGB)
            backToLubbyImg = aircv.cv2.cvtColor(aircv.imread("./img/backToLubby.png"), aircv.cv2.COLOR_BGR2RGB)
            matchLoseImg = aircv.cv2.cvtColor(aircv.imread("./img/matchLose.png"), aircv.cv2.COLOR_BGR2RGB)
            reachLimitImg = aircv.cv2.cvtColor(aircv.imread("./img/reachLimit.png"), aircv.cv2.COLOR_BGR2RGB)

            matchDefaultTime = 330
            matchLoseTimes = 0
            matchTimes = 0

            while self.startTimes>0:
                
                startMatchResult = self.__clickImgPosition(startMatchImg)
                if not startMatchResult:
                    self.emitLog.emit("未搜尋到配對按鈕")
                    continue
                self.emitLog.emit(f"> 第{matchTimes+1}場比賽開始 <")
                self.emitLog.emit("開始配對")
                self.startTimes -= 1
                self.__threadSleep(5)
                reachLimit = self.__clickImgPosition(reachLimitImg)
                if reachLimit:
                    self.emitLog.emit("已到達配對最高上限次數")
                    break
                matchTimes += 1
                matching = True
                matchFinish = False
                backToLubby = False

                self.__threadSleep(matchDefaultTime, 30)
                while matching == True:
                    matchingResult = self.__findImgfromScreenshot(matchingImg)
                    if matchingResult:
                        self.__threadSleep(30)
                    else:
                        matching = False
                self.__threadSleep(10)
                while not matchFinish:
                    matchFinishResult = self.__clickImgPosition(matchFinishImg)
                    if matchFinishResult:
                        matchFinish = True
                        self.emitLog.emit("比賽結束")
                    else:
                        self.__threadSleep(3)
                self.__threadSleep(5)

                matchLoseResult = self.__findImgfromScreenshot(matchLoseImg)
                if matchLoseResult:
                    matchLoseTimes += 1
                    self.emitLog.emit("失敗")
                else:
                    self.emitLog.emit("獲勝")
                
                while not backToLubby:
                    backToLubbyResult = self.__clickImgPosition(backToLubbyImg)
                    if backToLubbyResult:
                        self.emitLog.emit("返回大廳")
                        backToLubby = True
                    else:
                        self.__threadSleep(1)
                        
                self.__threadSleep(21)
                
            if self.startTimes <=0:
                self.emitLog.emit(f"AFK mode finish (times:{self.startTimes})")
                if (matchTimes>0):
                    self.emitLog.emit(f"共進行了{matchTimes}場，共贏了{matchTimes-matchLoseTimes}場，勝率為 {(matchTimes-matchLoseTimes)/matchTimes*100:.2f}%")
                self.isFinish.emit()
                
        except Exception as exc:
            print(exc)
            self.emitLog.emit(str(exc))
            self.isError.emit()

    def __clickImgPosition(self, img):
        findResult = self.__findImgfromScreenshot(img)
        if findResult:
            QtCore.QThread.sleep(3)
            if self.randomClick:
                leftbot, lefttop, rightbot, righttop = findResult['rectangle']
                left = leftbot[0]
                right = rightbot[0]
                top = lefttop[1]
                bot = rightbot[1]
                shiftX = left+int((right-left)*random.random()*0.3)
                shiftY = bot+int((top-bot)*random.random()*0.3)
                self.device.click(shiftX, shiftY)
            else:
                self.device.click(*findResult['result'])
            return True
        return False
    def __registerADBDeivce(self):
        device = adb.device(serial=self.connectPort)
        try:
            device.info
            self.device = device
            self.emitLog.emit("adb連接成功")
        except Exception as exc:
            self.emitLog.emit("adb連接失敗")
            raise exc
    

    def __threadSleep(self, second, randomSecond=None):
        if self.randomTime:
            sleepMillisecond = second * 1000
            if randomSecond:
                QtCore.QThread.msleep(sleepMillisecond + random.randint(-int(randomSecond*1000), int(randomSecond*1000)))
            else:
                QtCore.QThread.msleep(sleepMillisecond + random.randint(-int(sleepMillisecond/3), int(sleepMillisecond/3)))

        else:
            QtCore.QThread.sleep(second)

    def __findImgfromScreenshot(self, img, thres=0.9):
        if self.device :
            screenshot = np.asarray(self.device.screenshot())
            posit = aircv.find_template(screenshot, img, thres)
            print(posit)
            return posit
        return None

class Ui_Main(object):
    start = False
    def setupUi(self, Main):
        Main.setObjectName("Main")
        Main.resize(310, 460)
        Main.setMinimumSize(QtCore.QSize(310, 460))
        Main.setMaximumSize(QtCore.QSize(310, 460))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        Main.setFont(font)
        self.tabWidget = QtWidgets.QTabWidget(parent=Main)
        self.tabWidget.setGeometry(QtCore.QRect(5, 5, 300, 450))
        self.tabWidget.setMinimumSize(QtCore.QSize(300, 450))
        self.tabWidget.setMaximumSize(QtCore.QSize(300, 450))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        self.tabWidget.setFont(font)
        self.tabWidget.setAutoFillBackground(False)
        self.tabWidget.setStyleSheet("")
        self.tabWidget.setObjectName("tabWidget")
        self.functionTab = QtWidgets.QWidget()
        self.functionTab.setMinimumSize(QtCore.QSize(300, 450))
        self.functionTab.setMaximumSize(QtCore.QSize(300, 450))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        self.functionTab.setFont(font)
        self.functionTab.setObjectName("functionTab")
        self.matchTimes = QtWidgets.QLineEdit(parent=self.functionTab)
        self.matchTimes.setGeometry(QtCore.QRect(140, 70, 70, 20))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        self.matchTimes.setFont(font)
        self.matchTimes.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.matchTimes.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.matchTimes.setObjectName("matchTimes")
        self.connectPortTextShowLabel = QtWidgets.QLabel(parent=self.functionTab)
        self.connectPortTextShowLabel.setGeometry(QtCore.QRect(40, 20, 71, 21))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        self.connectPortTextShowLabel.setFont(font)
        self.connectPortTextShowLabel.setObjectName("connectPortTextShowLabel")
        self.startButton = QtWidgets.QPushButton(parent=self.functionTab)
        self.startButton.setGeometry(QtCore.QRect(140, 360, 100, 40))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        self.startButton.setFont(font)
        self.startButton.setStyleSheet("")
        self.startButton.setDefault(False)
        self.startButton.setFlat(False)
        self.startButton.setObjectName("startButton")
        self.startButton.clicked.connect(self.startPressEvent)
        self.covenantTimeLabel = QtWidgets.QLabel(parent=self.functionTab)
        self.covenantTimeLabel.setGeometry(QtCore.QRect(220, 70, 20, 20))
        self.covenantTimeLabel.setObjectName("covenantTimeLabel")
        self.logTextBrowser = QtWidgets.QTextBrowser(parent=self.functionTab)
        self.logTextBrowser.setGeometry(QtCore.QRect(40, 170, 200, 171))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(10)
        self.logTextBrowser.setFont(font)
        self.logTextBrowser.setObjectName("logTextBrowser")
        self.connectPort = QtWidgets.QLineEdit(parent=self.functionTab)
        self.connectPort.setGeometry(QtCore.QRect(120, 20, 140, 20))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        self.connectPort.setFont(font)
        self.connectPort.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.connectPort.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.connectPort.setObjectName("connectPort")
        self.matchTimesTextShowLabel = QtWidgets.QLabel(parent=self.functionTab)
        self.matchTimesTextShowLabel.setGeometry(QtCore.QRect(40, 70, 65, 20))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(12)
        self.matchTimesTextShowLabel.setFont(font)
        self.matchTimesTextShowLabel.setObjectName("matchTimesTextShowLabel")
        self.randomTimeCheckButton = QtWidgets.QCheckBox(parent=self.functionTab)
        self.randomTimeCheckButton.setGeometry(QtCore.QRect(40, 110, 101, 16))
        self.randomTimeCheckButton.setChecked(True)
        self.randomTimeCheckButton.setObjectName("randomTimeCheckButton")
        self.randomClickCheckButton = QtWidgets.QCheckBox(parent=self.functionTab)
        self.randomClickCheckButton.setGeometry(QtCore.QRect(40, 140, 121, 16))
        self.randomClickCheckButton.setChecked(True)
        self.randomClickCheckButton.setObjectName("randomClickCheckButton")
        self.line = QtWidgets.QFrame(parent=self.functionTab)
        self.line.setGeometry(QtCore.QRect(10, 50, 270, 3))
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.tabWidget.addTab(self.functionTab, "")

        self.retranslateUi(Main)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Main)

        self.worker = allstarWorker()
        self.worker.isStart.connect(self.startWorker)
        self.worker.isFinish.connect(self.stopWorker)
        self.worker.isError.connect(self.errorWorker)
        self.worker.emitLog.connect(lambda text: self.logTextBrowser.append(text))

    def retranslateUi(self, Main):
        _translate = QtCore.QCoreApplication.translate
        Main.setWindowTitle(_translate("Main", "王朝模式掛機工具"))
        self.matchTimes.setText(_translate("Main", "0"))
        self.connectPortTextShowLabel.setText(_translate("Main", "ADB位址"))
        self.startButton.setText(_translate("Main", "開始"))
        self.covenantTimeLabel.setText(_translate("Main", "次"))
        self.logTextBrowser.setHtml(_translate("Main", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'微軟正黑體\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">點擊開始啟動王朝自動掛機</p></body></html>"))
        self.randomTimeCheckButton.setText(_translate("Main", "隨機時間"))
        self.randomClickCheckButton.setText(_translate("Main", "隨機點擊位置"))
        self.connectPort.setText(_translate("Main", "emulator-5554"))
        self.matchTimesTextShowLabel.setText(_translate("Main", "對戰次數"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.functionTab), _translate("Main", "功能"))

    def startPressEvent(self):
        self.start = not self.start
        if self.start:
            IsRandomTime = self.randomTimeCheckButton.isChecked()
            IsRandomClick = self.randomClickCheckButton.isChecked()
            matchTimes = int(self.matchTimes.text()) if self.matchTimes.text().isdigit() else 0
            connectPort = str(self.connectPort.text())
            self.worker.setVariable(connectPort, matchTimes, IsRandomTime, IsRandomClick)
            self.worker.start()
        else:
            self.worker.terminate()
            self.logTextBrowser.append("===== 停止 =====")
            self.startProperty(False)

    def startProperty(self, isDisabled: bool):
        if isDisabled:
            self.startButton.setText("停止")
        else:
            self.startButton.setText("開始")
        self.connectPort.setDisabled(isDisabled)
        self.randomTimeCheckButton.setDisabled(isDisabled)
        self.randomClickCheckButton.setDisabled(isDisabled)
        self.matchTimes.setDisabled(isDisabled)

    def startWorker(self):
        self.logTextBrowser.setText("")
        self.startProperty(True)

    def errorWorker(self):
        self.start = False
        self.startProperty(False)

    def stopWorker(self):
        self.start = False
        self.startProperty(False)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("main.ico"))

    Main = QtWidgets.QWidget()
    ui = Ui_Main()
    ui.setupUi(Main)
    Main.show()
    sys.exit(app.exec())
