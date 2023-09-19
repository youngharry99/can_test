import streamlit as st
import pandas as pd
from func import *  # 封装功能

def clear_session_state():
    # Delete all the items in Session state
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
                st.sidebar.number_input(cmd_name, step=value_step, value=cmd_value,key=cmd_name)    # 可自定义输入

            elif cmd_type == ON_OFF_TYPE_FLAG: # 可选
                cmd_options = row.iloc[8][0].keys() # 选项提取
                st.sidebar.selectbox(cmd_name, options = cmd_options, index= 0,key=cmd_name)    # 可选
        return True
    except Exception as e:
        print('{0} show_Edit err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

def input_callback(cmd_name):
    try:
        cur_value = st.session_state[cmd_name]  # 获取对应的输入值
        row_data = raw_table_data.loc[raw_table_data['name'] == cmd_name]

        can_data = row_data['can_data']
        starting_byte = int(row_data['starting_byte'])  # 开始字节
        content_bits = int(row_data['content_bits'])    # 内容位数
        multiple = float(row_data['multiple'])          # 倍数
        offset = int(row_data['offset'])                # 偏移量
        hex_string = format(int(cur_value/multiple),'x')
        print('hex_string = ', hex_string)
        # 根据规则生成can_data
        #18DAF160#22 04 F3 04 61 04 90 04
    except Exception as e:
        print('{0} input_callback err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

def selected_callback(cmd_name):
    try:
        cur_value = st.session_state[cmd_name]  # 对应的输入值
        print('cur_value = ',cur_value)
        #example = raw_table_data.loc[raw_table_data['name'] == cmd_name,'example'].values[0]
        row = raw_table_data.loc[raw_table_data['name'] == cmd_name].index[0]   # 获取行
        example = raw_table_data.iloc[row,8]
        can_data = example[0][cur_value]
        # 更新dataframe
        raw_table_data.iloc[row,1] = can_data   # 更新can_data列
        raw_table_data.iloc[row,10] = cur_value # 更新 value 列
        print('update can_data:',can_data,';update value:', cur_value)

    except Exception as e:
        print('{0} selected_callback err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

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
                is_reverse = row_item['reverse']                # 是否反向
                hex_string = format(int((cur_value - offset)/multiple),'x') # 转成16进制字符串
                print('value:',cur_value,' hex_string:', hex_string)
                can_data = row_item['can_data']
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

if __name__ == '__main__':
    st.set_page_config(layout="wide",page_title='CAN Data')

    # 显示标题
    st.title(':blue[模拟 CAN Data] Platform')

    car_option = show_car_names()   # 界面显示车辆选择

    # 根据选择的car_option获取原始数据，
    raw_table_data = load_table_data('can_data_all_model', car_option)  # 原始数据

    # 对原始数据进行处理，缓存：导入CAN数据
    raw_table_data = import_can(raw_table_data)

    # 显示对应车型的可自定义功能
    show_Enable_Func()

    # 显示编辑选项
    show_Edit(raw_table_data)

    # 不断更新dataframe
    raw_table_data = ui_update_dataframe(raw_table_data)

    print(raw_table_data)
    # 显示表格
    st.dataframe(raw_table_data,use_container_width=True)
