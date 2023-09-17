import streamlit as st
import pandas as pd
from func import *  # 封装功能
st.set_page_config(layout="wide",
                   page_title='CAN Data')

# 显示标题
st.title(':blue[模拟 CAN Data] Platform')

# 显示选择车型
_car_options = load_car_names('can_data_all_model')
car_option = st.selectbox('选择车型', _car_options, index= 0)
print('选择车型:', car_option)

# 获取原始数据
raw_table_data = load_table_data('can_data_all_model', car_option)  # 原始数据

# 导入CAN数据
import_can(raw_table_data) # //
print(raw_table_data)

# 显示对应车型的可自定义功能
_func_options_list = list(raw_table_data.iloc[:,0])
func_selected = st.multiselect('可自定义功能', options = _func_options_list,default= _func_options_list)


def show_Edit():    # 初次显示编辑区
    try:
    # 显示对应功能的修改模块
        for pos, row in raw_table_data.iterrows():
            cmd_type = row.iloc[11]
            cmd_name = row.iloc[0]
            cmd_value = row.iloc[10]
            if cmd_type == CUSTOM_INPUT_TYPE_FLAG:  # 自定义输入类
                value_step = 1 if is_integer(cmd_value) else 0.01 # 判断value的值为int 或者是浮点型
                if value_step == 1: # 整型
                    cmd_value = int(cmd_value)
                elif value_step == 0.01:    # 浮点型
                    cmd_value = float(cmd_value)
                st.sidebar.number_input(cmd_name, step=value_step, value=cmd_value)

            elif cmd_type == ON_OFF_TYPE_FLAG: # 可选
                cmd_options = row.iloc[8][0].keys() # 选项提取
                st.sidebar.selectbox(cmd_name, options = cmd_options, index= 0)
    except Exception as e:
        print('{0} show_Edit err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

show_Edit()
# 显示表格
st.dataframe(raw_table_data)



