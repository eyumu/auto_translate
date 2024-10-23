#coding=utf-8
import os
import sys
import json
import requests
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import Tk, Label
from tkinterdnd2 import DND_FILES, TkinterDnD


# 设置 tkdnd 的路径（根据您的实际安装位置进行修改）
# 注意：_MEIPASS 是 PyInstaller 用于存储临时文件的目录
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
tkdnd_library_path = os.path.join(base_path, 'tcl/tkdnd2.8')  # 在此处替换为您的 tkdnd 安装目录相对路径
os.environ['TKDND_LIBRARY'] = tkdnd_library_path.replace('\\', '/')


class CommentedTreeBuilder(ET.TreeBuilder):
    def comment(self, text):
        self.start(ET.Comment, {})
        self.data(text)
        self.end(ET.Comment)


def translate(language, translate_texts):
    url = "http://192.168.1.226:8000/translate.php"
    lan = language.split('_')[1]
    translated_texts = []
    for text in translate_texts:
        data = {
            'lan': lan,  # 长度为 10 的字符串
            'str': text       # 长度为 4000 的字符串
        }
        print(data)
        # 向 API 发送 POST 请求
        response = requests.post(url, data=data)

        # 检查请求是否成功（HTTP 状态码为 200 表示成功）
        if response.status_code == 200:
            # 解析 JSON 响应
            #print(response.text)
            response_data = json.loads(response.text)

            # 提取 content 参数
            #content = response_data.get('content', None)
            content = response_data['choices'][0]['message']['content']

            if content is not None:
                print(content)
                translated_texts.append(content)
            else:
                print(language, "翻译失败")
        else:
            print(language, "请求失败，HTTP 状态码：", response.status_code)
        
    return translated_texts


def save_xml(file_path, language, translated_texts):
    # 获取文件路径和文件名
    dir_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    lan = language.split('_')[0]
    if lan == 'en':
        folder_name = "values"
    else:
        folder_name = "values-" + lan
    output_folder = os.path.join(dir_path, folder_name)
    #print(output_folder)
    # 创建 'values-fr' 文件夹（如果尚不存在）
    os.makedirs(output_folder, exist_ok=True)

    # 创建一个新的文件路径，在原始文件名后追加 language
    #new_file_path = os.path.splitext(file_path)[0] + '-' + language + os.path.splitext(file_path)[1]
    new_file_path = os.path.join(output_folder, file_name)
    #print(new_file_path)

    # 处理数组
    translat_text = []
    for translated_text in translated_texts:
        texts = translated_text.split('\n')
        for text in texts:
            if len(text) > 0:
                if '清空对话' not in text and '请按我的格式翻译' not in text:
                    translat_text.append(text)

    # 用于捕获注释的自定义解析器
    parser = ET.XMLParser(target=CommentedTreeBuilder())

    # 从文件读取 XML 内容并添加虚拟的根元素
    with open(file_path, "r", encoding="utf-8") as f:
        content = "".join(f.readlines())

    # 获取 XML 声明并从内容字符串中移除它
    xml_declaration = content.split("\n", 1)[0] if content.startswith("<?xml") else ""
    content = content.replace(xml_declaration, "", 1).strip()

    # 添加资源根元素并解析 XML
    root = ET.fromstring(f"<resources>{content}</resources>", parser=parser)

    # 遍历原xml文件
    ##root = ET.fromstring(xml_str, parser=parser)
    #tree = ET.parse(file_path, parser=parser)
    ##tree = ET.parse(file_path)
    #root = tree.getroot()
    
    #for elem, text in zip(root.findall(".//string"), translat_text):
    #    if elem.text is not None and elem.text.strip() != '':
    #        elem.text = text
    # 使用列表生成式筛选出 <string> 和 <string-array> 节点
    #elements = [elem for elem in root if elem.tag in {"string", "string-array"}]

    index = 0
    for elem in root.findall(".//string"):
        translatable = elem.get("translatable")
        if translatable == 'false':
            continue

        if index < len(translat_text):
            if elem.text is not None and elem.text.strip() != '':
                elem.text = translat_text[index]
                index += 1
        else:
            break

    # 将修改后的 XML 树转回字符串格式
    modified_xml_str = '' # ET.tostring(root, encoding='utf-8').decode('utf-8')
    for child in root:
        modified_xml_str += ET.tostring(child, encoding='utf-8').decode('utf-8')
    modified_xml_str = '<?xml version="1.0" encoding="utf-8"?>\n' + modified_xml_str

    # 保存新的xml文件 tree.write(new_file_path, encoding="utf-8")

    # 将修改后的 XML 树保存到一个新的文件中
    #with open(new_file_path, 'wb') as f:
        #f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')  # 添加 XML 声明
        #ET.ElementTree(root).write(f, encoding='utf-8', xml_declaration=True)
    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write(modified_xml_str)

    print('处理完文件：', new_file_path)
        
    
def load_xml(file_path):
    # Load the XML file and parse it
    tree = ET.parse(file_path)
    root = tree.getroot()

    translated_texts = []
    text_str = ''
    text_lens = 0

    for elem in root.findall(".//string"):
        #print(elem)
        translatable = elem.get("translatable")
        if translatable == 'false':
            continue

        text = elem.text
            
        if text is None:
            text_len = 0
        elif text.strip() == '':
            text_len = 0
        else:
            text = text.replace('\n', ' ').strip();
            text_len = len(text)

        if text_len > 0:
            if text_lens + text_len < 4000:
                text_lens += text_len + 2
                text_str += text + '\n'
            else:
                translated_texts.append(text_str)
                text_lens = text_len + 2
                text_str = text + '\n'

    if len(text_str) > 0:
        translated_texts.append(text_str)
    return translated_texts


def close_window():
    root.destroy()


def on_drop(event):
    # 获取所选语言
    selections = language_menu.curselection()
    if len(selections) == 0:
        print(f"请选择至少一种语言！")
        return 0
    
    languages = [language_options[i] for i in selections]
    
    # 获取文件
    file_path = event.data
    print(f"File path: {file_path}")
    if os.path.splitext(file_path)[1] != ".xml":
        print(f"这不是一个xml文件，请重新选择！")
        return 0
    
    close_window()
    print('读取 XML 文件中...')
    translate_texts = load_xml(file_path)
    #print(translate_texts)

    # 循环处理多个语言
    for language in languages:
        # 翻译
        print('开始翻译', language)
        translated_texts = translate(language, translate_texts)
        # 保存新的语言文件
        print(language, '翻译完成，保存文件中...')
        save_xml(file_path, language, translated_texts)

    print('全部处理完，请检查！')


if __name__ == '__main__':
    root = TkinterDnD.Tk()

    root.title("酷赛Android语言翻译工具V1.7")
    root.geometry("400x400")


    # 添加标签
    label = Label(root, text='1.请先选择要翻译的语言（可多选）', font=("Arial", 14), pady=10)
    label.pack(fill=tk.X, padx=10, pady=10)

    # 添加下拉菜单
    language_options = ['en_英语','zh-rCN_中文简体','zh-rHK_中文香港','zh-rTW_中文繁体','af_南非语','am_阿姆哈拉语','ar_阿拉伯语','as_阿萨姆语','az_阿塞拜疆语',
        'be_白俄罗斯语','bg_保加利亚语','ceb_菲律宾语','cs_捷克语','da_丹麦语','de_德语','el_希腊语','es_西班牙语','et_爱沙尼亚语','eu_巴士克语',
        'fa_波斯语','fi_芬兰语','fr_法语','ga_爱尔兰盖尔语','gd_苏格兰盖尔语','gl_加利西亚语','gu_印度古吉拉特语','he_希伯来语','hi_印地语',
        'hr_克罗地亚语','hu_匈牙利语','id_印度尼西亚语','is_冰岛语','it_意大利语','ja_日语','ka_乔治亚语','kn_卡纳拉语','ko_韩语','kok_孔卡尼语',
        'ky_吉尔吉斯斯坦语','lo_老挝语','lt_立陶宛语','luo_东苏丹语族尼罗语','lv_拉脱维亚语','mk_马其顿语','ml_马拉雅拉姆语','mn_蒙古语','mr_马拉地语',
        'ms_马来西亚语','mt_马尔代夫语','ne_尼泊尔语','nl_荷兰语','no_挪威语','or_奥里亚语','pa_旁遮普语','pl_波兰语','pt_葡萄牙语','qu_马丘达语','ro_罗马尼亚语',
        'ru_俄语','si_僧伽罗语','sk_斯洛伐克语','sl_斯洛文尼亚语','so_索马利亚语','sq_阿尔巴尼亚语','sr_塞尔维亚语','sv_瑞典语','sw_斯瓦希里语','ta_泰米尔语',
        'te_泰卢固语','th_泰语','tl_他加禄语','tr_土耳其语','uk_乌克兰语','uz_乌兹别克语','vi_越南语']


    language_var = tk.StringVar(root)
    language_menu = tk.Listbox(root, listvariable=language_var, selectmode='multiple', height=10, width=40)
    for option in language_options:
            language_menu.insert(tk.END, option)
    scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=language_menu.yview)
    language_menu.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    language_menu.pack(padx=10, pady=10)

    label = Label(root, text="2.然后拖拽英语或中文语言的xml文件\n到此处,随后查看后面DOS窗口的输出", font=("Arial", 14), pady=20)
    label.pack(fill=tk.X, padx=10, pady=10)

    label.drop_target_register(DND_FILES)
    label.dnd_bind('<<Drop>>', on_drop)

    root.mainloop()
    os.system('pause')
