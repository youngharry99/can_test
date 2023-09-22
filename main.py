import streamlit as st
import pandas as pd
from func import *  # 封装功能
from mqtt_test import CANTestThread
from streamlit.runtime.scriptrunner import add_script_run_ctx
import time
from streamlit_autorefresh import st_autorefresh

def session_state_init():
    # 更新broker 和 端口
    if 'broker' not in st.session_state and 'port' not in st.session_state:
        st.session_state['broker'] = config_info['broker']
        st.session_state['port'] = config_info['port']

    # 初始化更新table标志
    if 'update' not in st.session_state:
        st.session_state['update'] = 0
    # 初始化df
    if 'current_df' not in st.session_state:
        st.session_state['current_df'] = table_data
    # 初始化日志表格
    if 'log_df' not in st.session_state:    # 运行日志表格
        st.session_state['log_df'] = pd.DataFrame({
            'time':['a'],
            'message':['a'],
        })

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
    car_option = st.sidebar.selectbox('选择车型', _car_options, index= 0,on_change=change_car_callback)
    print('选择车型:'+ car_option)
    return car_option

# 显示对应车型的可自定义功能
def show_Enable_Func(dataframe):
    _func_options_list = list(dataframe.iloc[:,0])
    func = st.sidebar.expander('已采集功能')
    with func:
        st.multiselect('功能', options = _func_options_list,default= _func_options_list)
    return True

def show_Edit(dataframe):    # 初次显示编辑区
    #print('running show_Edit')
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
                st.selectbox(cmd_name, options = cmd_options, index= 0,key=cmd_name,on_change=trigger_update)    # 可选
        return True
    except Exception as e:
        print('{0} show_Edit err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

# 修改CAN数据
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

def ui_update_dataframe(dataframe): # 每次刷新根据session state更新dataframe
    #print('running ui_update_dataframe')
    try:
        if st.session_state['update'] == 1:

            for row, row_item in dataframe.iterrows():
                cmd_name = row_item.iloc[0]  # name
                cmd_type = row_item.iloc[11]  # type
                cmd_value = row_item.iloc[10]   # 表格value
                cur_value = st.session_state[cmd_name]   # 当前cmd对应session state的值

                if cmd_value == cur_value:  # 如果值相同，则跳过更新
                    continue

                if cmd_type == CUSTOM_INPUT_TYPE_FLAG:      # 自定义输入类型更新
                    starting_byte = int(row_item['starting_byte'])  # 开始字节
                    content_bits = int(row_item['content_bits'])    # 内容位数
                    multiple = float(row_item['multiple'])          # 倍数
                    offset = int(row_item['offset'])                # 偏移量
                    is_reverse = int(row_item['reverse'])                # 是否反向
                    hex_string = format(int((cur_value - offset)/multiple),'x').upper() # 转成16进制字符串
                    # print('value:',cur_value,' hex_string:', hex_string)
                    can_message = row_item.iloc[1]
                    replace_Can_Data(can_message, starting_byte, content_bits, hex_string, is_reverse)

                elif cmd_type == ON_OFF_TYPE_FLAG:          # 可选择类型更新
                    example = row_item.iloc[8]
                    can_data = example[0][cur_value]        # 取出待发送can数据
                    # 更新dataframe
                    dataframe.iloc[row,1] = can_data   # 更新can_data列
                    dataframe.iloc[row,10] = cur_value # 更新 value 列
                    print('Type 2 -> update can_data:',can_data,',value:', cur_value)

            print('update dataframe')
            st.session_state['current_df'] = dataframe  # 重新赋值

        st.session_state['update'] = 0  # 重置更新标志
        return True
    except Exception as e:
        print('{0} ui_update_dataframe err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))
        return False

def trigger_update():   # 编辑框触发更新dataframe
    st.session_state['update'] = 1   # 更新update标志

def start_test():   # 开启mqtt测试
    st.session_state['sended_times'] = 0
    st.session_state['running'] = True  # 开启线程运行

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
                      client_id=cur_client_id,password=cur_password,can_dataframe=None)
    add_script_run_ctx(t)
    if t:
        t.start()   # 启动线程
        st.toast(':blue[开启线程发送]',icon='💨')

def stop_test():    # 结束发送
    st.session_state['running'] = False # 停止线程标志位
    st.toast(':green[结束发送CAN]')

def clean_log():    # 清空日志
    if 'log_df' in st.session_state:
        st.session_state['log_df'] = pd.DataFrame({
            'time':['ok'],
            'message':[2],
        })
        st.toast('已清空日志')

if __name__ == '__main__':
    st.set_page_config(layout="wide",page_title='CAN Data')

    # 设置自动页面刷新
    st_autorefresh(interval=4 * 1000, key = 'test')

    # 显示标题
    st.title(':blue[模拟 CAN Data] Platform')

    # 读取配置文件
    config_info = read_config('config.json')

    # 界面显示车辆选择
    car_option = show_car_names()

    # 根据选择的 car_option 读取原始数据
    raw_table_data = load_table_data('can_data_all_model', car_option)

    # 对原始数据进行处理，缓存：导入CAN数据
    # 缓存会返回处理过后的数据副本
    table_data = import_can(raw_table_data)

    # 显示可用功能
    show_Enable_Func(table_data)

    # 显示编辑选项
    expander = st.sidebar.expander(label='自定义CAN',expanded=True)
    with expander:
        show_Edit(table_data)

    # 初始化session_state
    session_state_init()

    # 页面刷新，根据session state更新
    ui_update_dataframe(table_data)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:  # MQTT信息
        with st.form("user info"):
            st.text_input('终端SN',key='sn',value=config_info['sn'])
            st.text_input('username',key='username',value=config_info['userName'])
            st.text_input('client_id',key='client_id',value=config_info['client_id'])
            st.text_input('password',key='password',value=config_info['mqttPassword'])
            if 'running' not in st.session_state:
                button_disable = False
            else:
                button_disable = st.session_state['running']    # 禁止多开测试
            submit = st.form_submit_button('开始发送',on_click=start_test,disabled=button_disable)

    with col3:  # 日志
        st.write('运行日志')

        st.dataframe(st.session_state['log_df'],use_container_width=True,hide_index=True,height=300)
        st.button('清空',on_click=clean_log)

    with col2:  # 控制中心
        with st.status(':green[运行状态]',state='error',expanded=True) as status:
            if 'running' not in st.session_state:
                st.write('等待开始发送')

            elif st.session_state['running'] == True:
                st.write(':blue[正在向Broker发送CAN数据...]')
                if 'sended_times' in st.session_state:
                    sended_times = st.session_state['sended_times']
                    if sended_times > 0:
                        st.write('已发送次数: ',sended_times)
                status.update(label=':blue[运行中...]',state='running',expanded=True)
                st.button(':red[结束发送]', on_click=stop_test)

            elif st.session_state['running'] == False:
                st.write(':green[已断开MQTT连接...]')
                status.update(label=':green[发送结束]',state='complete',expanded=True)

        st.write('----待完善控制功能:')
        st.number_input('CAN发送时间间隔ms',value=200)

    session_df = st.session_state['current_df']
    #print(table_data)
    # 显示表格
    st.dataframe(session_df,use_container_width=True)
    st.write(st.session_state)
