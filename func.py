import streamlit as st
import read_file as rf
import time
import pandas as pd

CUSTOM_INPUT_TYPE_FLAG = 1
ON_OFF_TYPE_FLAG = 2


def time_value(dec):
    def wrapper(*args,**kwargs):
        start_time = time.time()
        get_str = dec(*args,**kwargs)
        end_time = time.time()
        print("函数运行共耗时：",end_time-start_time)
        return get_str
    return wrapper

#@st.cache_data
def load_car_names(fileName):   # 缓存:获取车辆类型
    return rf.get_Sheet_Names(fileName)

# 缓存:获取对应车辆的可自定义功能
#@st.cache_data
def load_table_data(fileName, carName):
    print('i ma here')
    df = rf.read_xlsx(fileName, carName)
    # 删除没有的CAN功能-> 根据 接收ID 是否为空判断
    df = df[df['接收ID'].notnull()]
    return df

# can数据格式化
def can_Data_Format(str_data:str):
    #str_data = "18DAF160#22 XX F3 04 61 04 90 04"
    #return "18DAF160#2200F30461049004"
    try:
        message = ''
        for char in str_data:
            if char == 'X' or char == 'x':
                char = '0'
            if char ==' ':
                continue
            message = message + char
        return message
    except Exception as e:
        print('can_data_format err', e)


def import_can(raw_table_data):# 导入can数据
    # 生成将要发送的can数据
    # 将示例变成字典存储
    try:
        for index, row in raw_table_data.iterrows():
            # 将示例转成字典存储
            data_list = [line.split('#') for line in row[8].strip().split('\n')]
            can_example_dict = {}
            for item in data_list:
                key = item[2]   # 取得键值
                value = item[0] + '#' + can_Data_Format(item[1])
                can_example_dict[key] = value

            # 将列表插入单元格中
            raw_table_data.iloc[index, 8] = [can_example_dict]
        return True
    except Exception as e:
        print(e)


if __name__ == '__main__':
    pass

