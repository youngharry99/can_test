import streamlit as st
import pandas as pd
from func import *  # 封装功能
from mqtt_test import CANTestThread

def clear_session_state():  # Delete all the items in Session state
    if st.session_state:
        for key in st.session_state.keys():
            del st.session_state[key]
    return True

def change_car_callback():  # 改变车辆时，清除原来所有session state
    if clear_session_state():
        print('{0} clear session state success!'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]')))

    return

# 显示选择车型,使用 缓存load_car_names数据
def show_car_names():   # 选择车型
    _car_options = load_car_names('can_data_all_model')
    car_option = st.selectbox('选择车型', _car_options, index= 0,on_change=change_car_callback)
    print('选择车型:'+ car_option)
    return car_option

# 显示对应车型的可自定义功能
def show_Enable_Func():
    _func_options_list = list(raw_table_data.iloc[:,0])
    st.multiselect('可自定义功能', options = _func_options_list,default= _func_options_list)
    return True

#@st.cache_data(experimental_allow_widgets=True)
def show_Edit(dataframe):    # 初次显示编辑区
    print('running show_Edit')
    try:
    # 显示对应功能的修改模块
        for pos, row in dataframe.iterrows():
            cmd_type = row.iloc[11]
            cmd_name = row.iloc[0]
            cmd_value = row.iloc[10]
            if cmd_type == CUSTOM_INPUT_TYPE_FLAG:  # 自定义输入类
                value_step = 1 if is_integer(cmd_value) else 0.01 # 判断value的值为int 或者是浮点型
                if value_step == 1: # 整型
                    cmd_value = int(cmd_value)
                elif value_step == 0.01:    # 浮点型
                    cmd_value = float(cmd_value)
                st.number_input(cmd_name, step=value_step, value=cmd_value,key=cmd_name)    # 可自定义输入

            elif cmd_type == ON_OFF_TYPE_FLAG: # 可选
                cmd_options = row.iloc[8][0].keys() # 选项提取
                st.selectbox(cmd_name, options = cmd_options, index= 0,key=cmd_name)    # 可选
        return True
    except Exception as e:
        print('{0} show_Edit err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

def replace_Can_Data(can_message:str, starting_byte : int, content_bits:int, hex_string:str, is_reverse:int):
    """_summary_
    Arguments:
        can_message {str} -- can报文    "12F95F50#00 00 00 00 00 00 11 22"\n
        starting_byte {int} -- 开始字节\n
        content_bits {int} -- 内容位数\n
        hex_string {str} -- 替换can_message的data部分\n
        is_reverse {int} -- 是否反向替换\n
    Return:
        message {str}   如果成功
        False           如果失败
    """
    # 18DAF160#22 04 F3 04 61 04 90 04#油量11.21L 0461
    # 12F85050#XX 5C 03 XX XX XX#转速860  035C
    try:
        message = can_message
        message_list = can_message.split('#')
        id = message_list[0]
        data = message_list[1]
        var_length  = int(content_bits/4)    # 内容位转成字符串长度

        if var_length%2 == 0:
            flag = 0
        else:
            flag = 1
        start_index = starting_byte*2 + flag
        end_index = starting_byte*2 + var_length + flag
        # 补零
        if var_length < len(hex_string):
            print('输入的value超出范围',hex_string)
            return False
        elif var_length > len(hex_string):
            hex_string = hex_string.zfill(var_length)   # 向前补零到var_length

        if is_reverse:  # 反向
            # 替换
            data = data[:start_index] + hex_string + data[end_index:]
            print('replace =', data)
        else:           # 不反向
            # 将字符串拆分成长度为2的子字符串列表
            pairs = [hex_string[i:i+2] for i in range(0, len(hex_string), 2)]
            # 对每个子字符串进行反转并连接起来s
            swapped_str = ''.join(pairs[::-1])
            data = data[:start_index] + swapped_str + data[end_index:]
            print('swapped_str', swapped_str)
            print('replace =', data)
        message = id + data
        return message
    except Exception as e:
        print('{0} replace_Can_Data err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

def ui_update_dataframe(dataframe): #每次刷新根据session state更新dataframe
    try:
        for row, row_item in dataframe.iterrows():
            cmd_name = row_item.iloc[0]  # name
            cmd_type = row_item.iloc[11]  # type

            cur_value = st.session_state[cmd_name]   # 当前cmd对应session state的值
            if cmd_type == CUSTOM_INPUT_TYPE_FLAG:      # 自定义输入类型
                starting_byte = int(row_item['starting_byte'])  # 开始字节
                content_bits = int(row_item['content_bits'])    # 内容位数
                multiple = float(row_item['multiple'])          # 倍数
                offset = int(row_item['offset'])                # 偏移量
                is_reverse = int(row_item['reverse'])                # 是否反向
                hex_string = format(int((cur_value - offset)/multiple),'x').upper() # 转成16进制字符串
                print('value:',cur_value,' hex_string:', hex_string)
                can_message = row_item.iloc[1]

                replace_Can_Data(can_message, starting_byte, content_bits, hex_string, is_reverse)


            elif cmd_type == ON_OFF_TYPE_FLAG:          # 可选择类型
                example = row_item.iloc[8]
                can_data = example[0][cur_value]        # 取出待发送can数据
                # 更新dataframe
                raw_table_data.iloc[row,1] = can_data   # 更新can_data列
                raw_table_data.iloc[row,10] = cur_value # 更新 value 列
                print('Type 2 -> update can_data:',can_data,',value:', cur_value)
        return raw_table_data
    except Exception as e:
        print('{0} ui_update_dataframe err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

def start_test():   # 开启mqtt测试
    # 连接MQTT服务器
    # 从session state获取信息
    cur_sn = st.session_state['sn']
    cur_client_id =st.session_state['client_id']
    cur_username = st.session_state['username']
    cur_password = st.session_state['password']
    cur_broker = st.session_state['broker']
    cur_port = st.session_state['port']
    # 创建测试线程
    t = CANTestThread(sn=cur_sn,broker=cur_broker,port=cur_port,username=cur_username,
                      client_id=cur_client_id,password=cur_password,can_dataframe=raw_table_data)
    if t:
        t.start()   # 启动线程



if __name__ == '__main__':
    st.set_page_config(layout="wide",page_title='CAN Data')

    # 显示标题
    st.title(':blue[模拟 CAN Data] Platform')

    config_info = read_config('config.json')    # 读取配置文件
    # 更新broker 和 端口
    if 'broker' not in st.session_state and 'port' not in st.session_state:
        st.session_state['broker'] = config_info['broker']
        st.session_state['port'] = config_info['port']

    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        with st.form("user info"):
            st.text_input('终端SN',key='sn',value=config_info['sn'])
            st.text_input('username',key='username',value=config_info['userName'])
            st.text_input('client_id',key='client_id',value=config_info['client_id'])
            st.text_input('password',key='password',value=config_info['mqttPassword'])
            # st.button('断开连接')
            st.form_submit_button('开始发送',on_click=start_test)

    with col2:
        st.write('控制中心')
        # MQTT状态
        with st.status(':orange[等待连接MQTT Broker]', state= 'error') as status:
            st.write('ok')
        st.button('停止发送')
        st.write(st.session_state)

    with col3:  # 日志列
        st.text_area('日志监控','''t was the best of times, it was the worst of times, it was
    the age of wisdom, it was the age of foolishness, it was
    the epoch of belief, it was the epoch of incredulity, it
    was the season of Light, it was the season of Darkness, it
    was the spring of hope, it was the winter of despai''',height=320)
        st.button('清空')

    car_option = show_car_names()   # 界面显示车辆选择

    # 根据选择的car_option获取原始数据，
    raw_table_data = load_table_data('can_data_all_model', car_option)  # 原始数据

    # 对原始数据进行处理，缓存：导入CAN数据
    raw_table_data = import_can(raw_table_data)

    # 显示对应车型的可自定义功能
    show_Enable_Func()

    expander = st.sidebar.expander('自定义CAN数据')
    with expander:
        # 显示编辑选项
        show_Edit(raw_table_data)

    # 不断更新dataframe
    raw_table_data = ui_update_dataframe(raw_table_data)

    #print(raw_table_data)
    # 显示表格
    st.dataframe(raw_table_data,use_container_width=True)

