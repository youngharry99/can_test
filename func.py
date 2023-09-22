import streamlit as st
import time
import pandas as pd
import os
import re
import logging
import json
CUSTOM_INPUT_TYPE_FLAG = 1
ON_OFF_TYPE_FLAG = 2

# 装饰器：计算函数运行时间
def time_value(dec):
    def wrapper(*args,**kwargs):
        start_time = time.time()
        get_str = dec(*args,**kwargs)
        end_time = time.time()
        print("函数运行共耗时：",end_time-start_time)
        return get_str
    return wrapper

@st.cache_data
def load_car_names(fileName):   # 缓存:获取车辆类型
    # 构建文件路径
    file_Path = f'./_xlsx/{fileName}.xlsx'
    if not os.path.exists(file_Path):
        file_Path = f'{fileName}.xlsx'
    # 打开目标文件
    work_excel = pd.ExcelFile(file_Path)
    return work_excel.sheet_names

# 缓存:获取对应车辆的可自定义功能
@st.cache_data
def load_table_data(fileName, carName):
    print('load_table_data()!!!!')
    try:
        # 构建文件路径
        file_Path = f'./_xlsx/{fileName}.xlsx'
        if not os.path.exists(file_Path):
            file_Path = f'{fileName}.xlsx'
        print('fileName: ', fileName, os.path.exists(file_Path))
        # 打开目标文件
        df = pd.read_excel(file_Path,sheet_name=carName,header=3,names=[
            'name','can_message','rec_id','length','starting_byte','content_bits','multiple','offset',
            'example','remark','value','type','reverse'])
        # 删除没有的CAN功能-> 根据 接收ID 是否为空判断
        df = df.dropna(subset=['rec_id'])
        # 重新分配行索引
        df = df.reset_index(drop=True)
        # 重新命名header

        df.iloc[:, 10] = df.iloc[:, 10].astype('str')   # value列
        df.iloc[:, 1] = df.iloc[:, 1].astype('str')     # can_data 列
        return df
    except Exception as e:
        print('{0} load_table_data err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

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

def extract_number(text):   # 提取字符串中的数字部分为字符串
    # 使用正则表达式找到匹配的数字
    match = re.search(r'\d+(\.\d+)?', text)
    if match:
        number_str = match.group()

    return number_str

def is_integer(s):  # 判断字符串否为整数
    try:
        int(s)
        return True
    except ValueError:
        return False

@st.cache_data
def import_can(data_table):# 导入can数据
    # 生成将要发送的can数据
    # 将示例变成字典存储
    print('running import_can()')
    try:
        for pos, row in data_table.iterrows():
            # 将示例转成字典存储
            data_list = [line.split('#') for line in row.iloc[8].strip().split('\n')]
            default_key = None  # 默认第一个键
            default_value = None  # 默认第一个值
            can_example_dict = {}   # 字典  {'value1:can_data1','value2:can_data2'}
            for index, item in enumerate(data_list):
                key = item[2]   # 取得键值
                value = item[0] + '#' + can_Data_Format(item[1])
                can_example_dict[key] = value

                if index == 0 :     # 默认：取第一个键值对放入value 和 command
                    default_key = key
                    default_can_data = value

            # 将can_example_dict字典变成列表插入example单元格中
            data_table.iloc[pos,8] = [can_example_dict]

            if row.loc['type'] == 1:    # 如果为自定义输入类型,提取其中的数字字符串
                default_key = extract_number(default_key)

            # 将初始化[默认为第一位]的 value插入value单元格中，default_can_data放入can_data
            data_table.iloc[pos,10] = default_key
            data_table.iloc[pos,1] = default_can_data
        return data_table
    except Exception as e:
        print('{0} import_can err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

def setup_logger(name):
    # 创建logger实例
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # # 创建一个文件处理器，用于将日志写入文件
    # file_handler = logging.FileHandler('logfile.log')
    # file_handler.setLevel(logging.INFO)

    # 创建一个控制台处理器，用于将日志输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建一个格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)

    # 将处理器添加到logger中
    #logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

@st.cache_data
def read_config(filename):  # 配置文件
    try:
        with open(filename, 'r') as config_file:
            config_data = json.load(config_file)
            # 获取默认值
            return config_data
    except Exception as e:
        print('{0} read_config err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))

if __name__ == '__main__':
    pass

