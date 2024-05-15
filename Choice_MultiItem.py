# 选择多个项目
def Choice_MultiItem(choices: list, prompt: str='选择多个项目，用 , 分隔', input_prompt: str='输入选中项目的数字：'):
    import pyinputplus
    print(prompt)
    for i in choices: print(f"{choices.index(i)}. {i}")
    seletc = []
    for i in pyinputplus.inputRegex(r'(\d+,?)+(\d+)?', prompt=input_prompt, default='0', limit=3).split(','):
        try: 
            seletc.append(choices[int(i)])
        except IndexError:
            pass

    return seletc
