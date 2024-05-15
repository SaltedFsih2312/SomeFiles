'''
这个脚本只是一时兴起去尝试以表格的方式显示字典数据
'''

from re import match

def is_dublechar(str):
    if match('[^\x00-\xff]', str):
        return True
    return False

def table(column: list, alias={}, width='', row=[{},{}], fill=' ', interval=' '):
    '''
    column：列，可以输出单独几个列，只要与行里的数据对应上就行，['column0', 'column1', ...]\n
    row：行，[{'column0': 'row0', 'column1': 'row1'}, {'column0': 'row3', 'column1': 'row4'}, ...]\n
    width：列宽（字符），整数类型是对全部列生效，使用列表控制可以控制单列列宽，但是列表中的元素数量要与列的元素数量对应\n
    fill：使用指定的字符填充，单个字符\n
    interval：每列间隔符
    alias：字段别名
    '''
    # 判断每一列的宽度
    # 每检测到一个双字节字符，最大长度就+1
    column_width = {}
    for item in column:
        try: alias_item = alias[item]
        except: alias_item = item

        column_width[item] = []

        # 处理列名的长度
        str_len = len(str(alias_item))
        for i in str(alias_item):
            if is_dublechar(i) == True: str_len += 1
        column_width[item].append(str_len)

        # 处理数据长度
        for key in row:
            str_len = len(str(key[item]))
            for i in str(key[item]):
                if is_dublechar(i) == True: str_len += 1
            column_width[item].append(str_len)

        # 只有提供的列宽值大于数据中最长字符串才生效
        if type(width) == type(1) and width > max(column_width[item]):    # 整数类型是对全部生效
            column_width[item].append(width)
        elif type(width) == type([]) and width[column.index(item)] > max(column_width[item]):    # 使用列表控制可以控制单列
            column_width[item].append(width[column.index(item)])

    # 输出首行
    for item in column:
        try: alias_item = alias[item]
        except: alias_item = item

        # 获取当前字符串的长度，为对齐时填充的空格提供数字
        chinese_count = 0
        for i in alias_item:
            if is_dublechar(i) == True: chinese_count += 1

        fill_num = max(column_width[item]) - len(str(alias_item)) - chinese_count
        if fill_num > 32: fill_num = 32

        # 如果是最后一个列则不添加空格，同时换行
        if item == column[-1]:
            print(str(alias_item))
        else:
            print(str(alias_item) + fill*(fill_num), end=interval)

    # 输出数据
    for key in row:
        for item in column:
            # 获取当前字符串的长度，为对齐时填充的空格提供数字
            chinese_count = 0
            for i in str(key[item]):
                if is_dublechar(i) == True: chinese_count += 1
            
            # 如果该行的最后一项，则不添加空格，同时换行
            if item == column[-1]:
                print(str(key[item]))
            else:
                print(str(key[item]) + fill*(max(column_width[item]) - len(str(key[item])) - chinese_count), end=interval)
