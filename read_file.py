# 从文件中获取数据
# import xlrd
import os
import time
import pandas as pd

# 读取xlsx指定sheet的全部数据
def read_xlsx(fileName, sheetName):
    try:
        # 构建文件路径
        file_Path = f'./_xlsx/{fileName}.xlsx'
        if not os.path.exists(file_Path):
            file_Path = f'{fileName}.xlsx'
        print('fileName: ', fileName, os.path.exists(file_Path))
        # 打开目标文件
        df = pd.read_excel(file_Path,sheet_name=sheetName,header=3)
        return df
    except Exception as e:
        print('{0} read_xlsx err:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), str(e)))
        print(e)

# 获取全部sheet Names
def get_Sheet_Names(fileName):
        # 构建文件路径
        file_Path = f'./_xlsx/{fileName}.xlsx'
        if not os.path.exists(file_Path):
            file_Path = f'{fileName}.xlsx'

        # 打开目标文件
        work_excel = pd.ExcelFile(file_Path)
        return work_excel.sheet_names

if __name__ == '__main__':
    sheet_list = get_Sheet_Names('can_data_all_model')
    print(sheet_list)
    data_list = read_xlsx('can_data_all_model', sheet_list[2])
    print('{0} read_xlsx list:{1}'.format(time.strftime('[%Y-%m-%d-%H:%M:%S]'), data_list))
