from machine import Pin, Timer
import bluetooth

SERVICE_UUID = b"0000fff0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = b"0000fff1-0000-1000-8000-00805f9b34fb"
UUID = [0xfb,0x34,0x9b,0x5f,0x80,0x00,0x00,0x80,0x00,0x10,0x00,0x00,0xf0,0xff,0x00,0x00]
class ESP32S3_BLE():
    def __init__(self, name):
        self.timer1 = Timer(0)
        self.name = name
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.config(gap_name=name)
        self.disconnected()
        self.ble.irq(self.ble_irq)
        self.register()
        self.advertiser()
        self.BLE_MESSAGE = ''  # 保存接收到的消息
        self.flag = 0
    def connected(self):
        self.timer1.deinit()
        self.flag = 1
        print("已连接")
    def disconnected(self):
        self.flag = 0
        print("断开连接")

    def ble_irq(self, event, data):
        # 根据事件类型处理
        if event == 1:
            self.connected()
        elif event == 2:
            self.advertiser()
            self.disconnected()
        elif event == 3:
            # 读取客户端发送的数据
            buffer = self.ble.gatts_read(self.rx)
            self.BLE_MESSAGE = buffer

    def register(self):
        # 注册服务和特征
        services = (
            (
                bluetooth.UUID(SERVICE_UUID),
                (
                    (bluetooth.UUID(CHARACTERISTIC_UUID), bluetooth.FLAG_WRITE),
                )
            ),
        )
        ((self.rx, ), ) = self.ble.gatts_register_services(services)

    def advertiser(self):
        # 广播设备名称
        name = bytes(self.name, 'UTF-8')
        adv_mode  = bytearray([0x02, 0x01, 0x06])  # BLE flags
        adv_uuid = bytearray([0x11, 0x07]) + bytearray(UUID)
        adv_data = adv_mode + adv_uuid
        self.ble.gap_advertise(100, adv_data)
