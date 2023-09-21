import paho.mqtt.client as mqtt
import time
import random
from func import setup_logger
import pandas as pd
import threading
import streamlit as st
# log = setup_logger(__name__)

class Mqtt_Client:
    def __init__(self, sn, broker, port, username = None, client_id = None, password = None) -> None:
        self.sn          = sn
        self.broker      = broker
        self.port        = port
        self.userName    = username
        self.client_id   = client_id
        self.mqttPassword= password
        self.topic       = 'S' + sn
        self.subTopic    = 'U/JSON/' + sn
        self.client_Init()

    def client_Init(self):
        self.client = mqtt.Client(self.client_id)

        self.client.username_pw_set(username=self.userName,password=self.mqttPassword)
        self.client.on_connect = self.on_connect  # connect callback
        self.client.on_message = self.on_message  # message callback
        self.client.on_subscribe = self.on_subscribe  # subscribe callback

    def connect_mqtt(self):
        self.client.connect(self.broker, self.port, 60)   # 连接服务器
        self.client.loop_start()    # 开始监听

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connect MQTT Server Success")
            #订阅终端发布主题
            self.client.subscribe(self.subTopic)
        elif rc == 4:
            print('Connect MQTT Server Fail:name or password wrong')

    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))

    def on_subscribe(client, userdata, mid, grated_qos, properties=None):
        print('subscribe success!')

    def publish(self, message):
        paylad = '5,3,1677235643,' + str(random.randint(1000, 3000)) + ',34383038,' + message
        self.client.publish(self.topic, paylad)
        print(f"Published message: {message}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print('已经断开连接')

class CANTestThread(threading.Thread):
    def __init__(self,sn,broker, port, username, client_id, password,can_dataframe,call_back = None):
        threading.Thread.__init__(self)  # 调用父类初始化
        self.sn = sn
        self.broker = broker
        self.port = port
        self.username = username
        self.client_id = client_id
        self.password = password
        self.can_dataframe = can_dataframe
        #self.toast = call_back

    def run(self) -> None:      # 重写线程run方法
        try:
            client = Mqtt_Client(sn=self.sn,broker=self.broker, port= self.port, username=self.username, client_id= self.client_id, password=self.password)
            client.connect_mqtt()        # 连接mqtt

            
            sended_times = 0    # 发送次数
            while(1):
                # 遍历发送数据
                for pos, row in self.can_dataframe.iterrows():
                    can_message = row.iloc[1]
                    cmd = 'CANSEND=' + can_message
                    if st.session_state['running'] == True:
                        client.publish(cmd)
                    else:
                        client.disconnect()
                        # st.toast(':red[结束发送CAN]')
                        print('threading is dead')
                        return
                    time.sleep(1)
                sended_times = sended_times + 1
                print('sended_times = ', sended_times)
                st.session_state['sended_times'] = sended_times #更新send_times

            client.disconnect()
            print("is_connected",client.client.is_connected())
        except Exception as e:
            print('{0} mqtt_can_test err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

if __name__ == '__main__':
    pass
