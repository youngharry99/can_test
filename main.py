import streamlit as st
import pandas as pd
from func import *  # 封装功能
import read_file as rf
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

try:
    # 显示对应功能的修改模块
    pass

except Exception as e:
    print(e)

