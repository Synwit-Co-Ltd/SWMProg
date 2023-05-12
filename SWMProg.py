#! python3
import os
import sys
import collections
import configparser

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog

import jlink
import xlink
import device


Lang = 'cn'


os.environ['PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libusb-1.0.24/MinGW64/dll') + os.pathsep + os.environ['PATH']



'''
from SWMProg_UI import Ui_SWMProg
class SWMProg(QWidget, Ui_SWMProg):
    def __init__(self, parent=None):
        super(SWMProg, self).__init__(parent)
        
        self.setupUi(self)
'''
class SWMProg(QWidget):
    def __init__(self, parent=None):
        super(SWMProg, self).__init__(parent)
        
        uic.loadUi('SWMProg.ui', self)

        self.setWindowTitle(f'{self.windowTitle()} v2.7.5')
        
        self.table.setVisible(False)
        self.resize(self.width(), 160)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.prgInfo.setVisible(False)

        self.savePath = ''
        
        self.initSetting()

        self.tmrDAP = QtCore.QTimer()
        self.tmrDAP.setInterval(1000)
        self.tmrDAP.timeout.connect(self.on_tmrDAP_timeout)
        self.tmrDAP.start()

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w', encoding='utf-8')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini', encoding='utf-8')
        
        if not self.conf.has_section('globals'):
            self.conf.add_section('globals')
            self.conf.set('globals', 'mcu',  'SWM181xB')
            self.conf.set('globals', 'addr', '0 K')
            self.conf.set('globals', 'size', '16 K')
            self.conf.set('globals', 'link', '')
            self.conf.set('globals', 'dllpath', '')
            self.conf.set('globals', 'hexpath', '[]')

        self.cmbMCU.addItems(device.Devices.keys())
        self.cmbMCU.setCurrentIndex(self.cmbMCU.findText(self.conf.get('globals', 'mcu')))

        self.cmbAddr.setCurrentIndex(self.cmbAddr.findText(self.conf.get('globals', 'addr')))
        self.cmbSize.setCurrentIndex(self.cmbSize.findText(self.conf.get('globals', 'size')))
        
        self.cmbDLL.addItem(self.conf.get('globals', 'dllpath'))
        self.on_tmrDAP_timeout()    # add DAPLink

        index = self.cmbDLL.findText(self.conf.get('globals', 'link'))
        self.cmbDLL.setCurrentIndex(index if index != -1 else 0)

        self.cmbHEX.addItems(eval(self.conf.get('globals', 'hexpath')))

        if self.conf.has_option('globals', 'lang') and self.conf.get('globals', 'lang') == 'en':
            self.lblMCU.setText('MCU :')
            self.lblDLL.setText('DLL :')
            self.lblHEX.setText('BIN :')
            self.lblAddr.setText('Addr:')
            self.lblSize.setText('Size:')
            self.btnErase.setText('Erase')
            self.btnWrite.setText('Write')
            self.btnRead.setText('Read')

            global Lang
            Lang = 'en'

    def on_tmrDAP_timeout(self):
        if not self.isEnabled():    # link working
            return

        try:
            from pyocd.probe import aggregator
            self.daplinks = aggregator.DebugProbeAggregator.get_all_connected_probes()
            if len(self.daplinks) != self.cmbDLL.count() - 1:
                for i in range(1, self.cmbDLL.count()):
                    self.cmbDLL.removeItem(i)
                for i, daplink in enumerate(self.daplinks):
                    self.cmbDLL.addItem(daplink.product_name)
        except Exception as e:
            pass

    def connect(self):
        try:
            if self.cmbDLL.currentIndex() == 0:
                self.xlk = xlink.XLink(jlink.JLink(self.cmbDLL.currentText(), device.Devices[self.cmbMCU.currentText()].CHIP_CORE))

            else:
                from pyocd.coresight import dap, ap, cortex_m
                daplink = self.daplinks[self.cmbDLL.currentIndex() - 1]
                daplink.open()

                _dp = dap.DebugPort(daplink, None)
                _dp.init()
                _dp.power_up_debug()

                _ap = ap.AHB_AP(_dp, 0)
                _ap.init()

                self.xlk = xlink.XLink(cortex_m.CortexM(None, _ap))

            self.dev = device.Devices[self.cmbMCU.currentText()](self.xlk)

        except Exception as e:
            QMessageBox.critical(self, tr('连接失败'), str(e), QMessageBox.Yes)

            return False

        return True

    @pyqtSlot()
    def on_btnChipErase_clicked(self):
        if self.connect():
            self.setEnabled(False)
            self.prgInfo.setVisible(True)

            self.threadErase = ThreadAsync('erase', self.dev.chip_erase)
            self.threadErase.taskFinished.connect(self.on_btnErase_finished)
            self.threadErase.start()

    @pyqtSlot()
    def on_btnErase_clicked(self):
        if self.connect():
            self.setEnabled(False)
            self.prgInfo.setVisible(True)

            self.threadErase = ThreadAsync('erase', self.dev.sect_erase, self.addr, self.size)
            self.threadErase.taskFinished.connect(self.on_btnErase_finished)
            self.threadErase.start()

    def on_btnErase_finished(self):
        QMessageBox.information(self, tr('擦除完成'), f'        {tr("芯片擦除完成")}        ', QMessageBox.Yes)

        if self.cmbMCU.currentText() not in ['SWM320_SDRAM', 'SWM341_SDRAM']:   # 防止复位 SDRAM 配置
            self.xlk.reset()
        self.xlk.close()

        self.setEnabled(True)
        self.prgInfo.setVisible(False)

    @pyqtSlot()
    def on_btnWrite_clicked(self):
        if self.connect():
            self.setEnabled(False)
            self.prgInfo.setVisible(True)

            filePath = self.cmbHEX.currentText()
            if not os.path.exists(filePath):
                QMessageBox.warning(self, tr('文件不存在'), filePath, QMessageBox.Yes)
                return

            if filePath.endswith('.ini'):
                self.ProgData = {}
                for i in range(self.table.rowCount()):
                    if self.table.item(i, 0).checkState():
                        filePath = self.table.item(i, 2).text()
                        if not os.path.exists(filePath):
                            QMessageBox.warning(self, tr('文件不存在'), filePath, QMessageBox.Yes)
                            return

                        if filePath.endswith('.hex'): data = parseHex(filePath)
                        else:                         data = open(filePath, 'rb').read()
                        self.ProgData[self.table.item(i, 0).text()] = {'addr': int(self.table.item(i, 1).text(), 16), 'data': data}
            else:
                if filePath.endswith('.hex'):
                    self.ProgData = {'APP': {'addr': self.addr, 'data': parseHex(filePath)}}
                else:
                    self.ProgData = {'APP': {'addr': self.addr, 'data': open(filePath, 'rb').read()}}
            
            for prog in self.ProgData.values():
                if len(prog['data'])%self.dev.SECT_SIZE:
                    prog['data'] = prog['data'] + b'\xFF' * (self.dev.SECT_SIZE - len(prog['data'])%self.dev.SECT_SIZE)
            
            self.threadWrite = ThreadAsync('write', self.dev.chip_write, *self.ProgData.values())
            self.threadWrite.taskFinished.connect(self.on_btnWrite_finished)
            self.threadWrite.start()

    def on_btnWrite_finished(self):
        QMessageBox.information(self, tr('烧写完成'), f'        {tr("程序烧写完成")}        ', QMessageBox.Yes)

        if self.cmbMCU.currentText() not in ['SWM320_SDRAM', 'SWM341_SDRAM']:   # 防止复位 SDRAM 配置
            self.xlk.reset()
        self.xlk.close()
        
        self.setEnabled(True)
        self.prgInfo.setVisible(False)

    @pyqtSlot()
    def on_btnRead_clicked(self):
        if self.connect():
            self.setEnabled(False)
            self.prgInfo.setVisible(True)

            self.RdBuffer = []  # bytes 无法 extend，因此用 list

            self.threadRead = ThreadAsync('read', self.dev.chip_read, self.addr, self.size, self.RdBuffer)
            self.threadRead.taskFinished.connect(self.on_btnRead_finished)
            self.threadRead.start()

    def on_btnRead_finished(self):
        binpath, filter = QFileDialog.getSaveFileName(caption=tr('将读取到的数据保存到文件'), filter=f'{tr("程序文件")} (*.bin)')
        if binpath:
            with open(binpath, 'wb') as f:
                f.write(bytes(self.RdBuffer))

        if self.cmbMCU.currentText() not in ['SWM320_SDRAM', 'SWM341_SDRAM']:   # 防止复位 SDRAM 配置
            self.xlk.reset()
        self.xlk.close()

        self.setEnabled(True)
        self.prgInfo.setVisible(False)

    @property
    def addr(self): return int(self.cmbAddr.currentText().split()[0]) * 1024

    @property
    def size(self): return int(self.cmbSize.currentText().split()[0]) * 1024

    @pyqtSlot(int)
    def on_cmbMCU_currentIndexChanged(self, indx):
        dev = device.Devices[self.cmbMCU.currentText()]

        self.cmbAddr.clear()
        self.cmbSize.clear()
        for i in range(dev.CHIP_SIZE//dev.SECT_SIZE):
            if (dev.SECT_SIZE * i) % 1024 == 0:
                self.cmbAddr.addItem('%d K' %(dev.SECT_SIZE * i     // 1024))
            if (dev.SECT_SIZE * (i+1)) % 1024 == 0:
                self.cmbSize.addItem('%d K' %(dev.SECT_SIZE * (i+1) // 1024))

        self.cmbAddr.setCurrentIndex(self.cmbAddr.findText(self.conf.get('globals', 'addr')))
        self.cmbSize.setCurrentIndex(self.cmbSize.findText(self.conf.get('globals', 'size')))

        if self.cmbMCU.currentText() in ('SWM211', 'SWM341'):
            self.btnChipErase.setEnabled(True)
        else:
            self.btnChipErase.setEnabled(False)

    @pyqtSlot()
    def on_btnDLL_clicked(self):
        dllpath, filter = QFileDialog.getOpenFileName(caption=f'JLink_x64.dll {tr("路径")}', filter=f'{tr("动态链接库")} (*.dll)', directory=self.cmbDLL.itemText(0))
        if dllpath:
            self.cmbDLL.setItemText(0, dllpath)

    @pyqtSlot()
    def on_btnHEX_clicked(self):
        hexpath, filter = QFileDialog.getOpenFileName(caption=tr('程序文件路径'), filter=f'{tr("程序文件")} (*.bin *.hex *.ini)', directory=self.cmbHEX.currentText())
        if hexpath:
            self.cmbHEX.insertItem(0, hexpath)
            self.cmbHEX.setCurrentIndex(0)

    @pyqtSlot(str)
    def on_cmbHEX_currentIndexChanged(self, text):
        if text.endswith('.ini'):
            self.table.setVisible(True)
            self.resize(self.width(), 270)

            conf = configparser.ConfigParser()
            conf.read(text, encoding='gbk')
            self.table.setRowCount(len(conf.sections()))
            for i,section in enumerate(conf.sections()):
                checkbox = QtWidgets.QTableWidgetItem(section)
                checkbox.setCheckState(QtCore.Qt.Checked)
                self.table.setItem(i, 0, checkbox)
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(conf.get(section, 'addr')))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(conf.get(section, 'path')))
        else:
            self.table.setVisible(False)
            self.resize(self.width(), 160)

    @pyqtSlot(int, int)
    def on_table_cellDoubleClicked(self, row, column):
        if column != 2: # 只能设置文件路径
            return

        hexpath, filter = QFileDialog.getOpenFileName(caption=tr('程序文件路径'), filter=f'{tr("程序文件")} (*.bin *.hex)', directory=self.table.item(row, column).text())
        if hexpath:
            self.table.setItem(row, column, QtWidgets.QTableWidgetItem(hexpath))

            conf = configparser.ConfigParser()
            conf.read(self.cmbHEX.currentText(), encoding='gbk')
            conf.set(self.table.item(row, 0).text(), 'path', hexpath)
            conf.write(open(self.cmbHEX.currentText(), 'w', encoding='gbk'))
    
    def closeEvent(self, evt):
        self.conf.set('globals', 'mcu',  self.cmbMCU.currentText())
        self.conf.set('globals', 'addr', self.cmbAddr.currentText())
        self.conf.set('globals', 'size', self.cmbSize.currentText())
        self.conf.set('globals', 'link', self.cmbDLL.currentText())
        self.conf.set('globals', 'dllpath', self.cmbDLL.itemText(0))

        hexpath = [self.cmbHEX.currentText()] + [self.cmbHEX.itemText(i) for i in range(self.cmbHEX.count())]
        self.conf.set('globals', 'hexpath', repr(list(collections.OrderedDict.fromkeys(hexpath))))    # 保留顺序去重    

        self.conf.write(open('setting.ini', 'w', encoding='utf-8'))


class ThreadAsync(QtCore.QThread):
    taskFinished = QtCore.pyqtSignal()

    def __init__(self, oper, func, *args):
        super(ThreadAsync, self).__init__()
        self.oper = oper
        self.func = func
        self.args = args

    def run(self):
        if self.oper == 'write':
            for file in self.args:
                self.func(file['addr'], file['data'])
        else:
            self.func(*self.args)
        
        self.taskFinished.emit()


def parseHex(file):
    ''' 解析 .hex 文件，提取出程序代码，没有值的地方填充0xFF '''
    data = ''
    currentAddr = 0
    extSegAddr  = 0     # 扩展段地址
    for line in open(file, 'rb').readlines():
        line = line.strip()
        if len(line) == 0: continue
        
        len_ = int(line[1:3],16)
        addr = int(line[3:7],16) + extSegAddr
        type = int(line[7:9],16)
        if type == 0x00:
            if currentAddr != addr:
                if currentAddr != 0:
                    data += '\xFF' * (addr - currentAddr)
                currentAddr = addr
            for i in range(len_):
                data += chr(int(line[9+2*i:11+2*i], 16))
            currentAddr += len_
        elif type == 0x02:
            extSegAddr = int(line[9:9+4], 16) * 16
        elif type == 0x04:
            extSegAddr = int(line[9:9+4], 16) * 65536
    
    return data.encode('latin')


def tr(word: str) -> str:
    if Lang == 'cn':
        return word

    else:
        return {
            '连接失败': 'Connect Fail',
            '擦除完成': 'Erase Done',
            '芯片擦除完成': 'Chip Erase Done',
            '文件不存在': 'File Not Exist',
            '烧写完成': 'Write Done',
            '程序烧写完成': 'Program Write Done',
            '将读取到的数据保存到文件': 'Save the read data to a file',
            '程序文件': 'Program File',
            '路径': 'Path',
            '动态链接库': 'Dynamic Link Library',
            '程序文件路径': 'Program File Path',
        }[word]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mcu = SWMProg()
    mcu.show()
    app.exec()
