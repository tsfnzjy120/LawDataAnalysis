# -*- coding:utf-8 -*


import ujson
import pymysql
import zlib
import base64
from paper_parser import settings
import re
from datetime import datetime
import jieba.posseg as pseg
import numpy as np


class MysqlConnector:

    def __init__(self, user_id=1):  # 传入用户id，0-root权限 1-读取权限，默认1
        self.db = pymysql.connect(
            host=settings.MysqlParameter.host, port=settings.MysqlParameter.port,
            user=settings.MysqlParameter.users[user_id], passwd=settings.MysqlParameter.passwds[user_id],
            db=settings.MysqlParameter.database, charset=settings.MysqlParameter.charset
        )
        self.cursor = self.db.cursor()

    def __enter__(self):
        max_id_sql = 'select max(id) from {}'.format(settings.MysqlParameter.used_table)
        self.cursor.execute(max_id_sql)
        self.max_id = int(self.cursor.fetchone()[0])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.db.close()


class PaperContentCoder:

    @staticmethod
    def check_json(json_str):
        is_json = True
        try:
            ujson.loads(json_str)
        except ValueError:
            is_json = False
        return is_json

    @classmethod
    def encode(cls, json_str):
        """ json_str -> bs64_str """
        if cls.check_json(json_str):
            json_encoded = base64.b64encode(zlib.compress(json_str.encode())).decode()
        else:
            json_encoded = None
        return json_encoded

    @classmethod
    def decode(cls, bs64_str):
        """ bs64_str -> json_str """
        json_decoded = zlib.decompress(base64.b64decode(bs64_str.encode())).decode()
        if not cls.check_json(json_decoded):
            json_decoded = None
        return json_decoded


class TagAlter:
    """ 以root用户登录数据库，批量调整tag值 """
    def __init__(self, alter_ids, tag_value):
        self.alter_ids = alter_ids  # 需要修改的row_id list[int, ]
        self.tag = tag_value  # 修改后的tag值 int

    def alter(self):
        with MysqlConnector(0) as mc:
            update_sql = 'update {0} set tag = {1} where id={{}}'.format(settings.MysqlParameter.used_table, self.tag)
            for row_id in self.alter_ids:
                mc.cursor.execute(update_sql.format(row_id))
                mc.db.commit()
                print('row_id {} has changed tag to {}'.format(row_id, self.tag))
        return 0


class TextProcessor:
    """ 文本处理器，包含各种文本处理函数 """
    PUNCS = r""",.?!:;()"'-，。？！：；（）“”‘’《》、"""
    NUMS = '0123456789'

    def __init__(self, text):
        self.text = text

    @property
    def clean_text(self):
        """ 文本内容清洗 """
        clean_text = ''
        if self.text:
            clean_text = self.text.strip()
            clean_text = clean_text.replace('\n', '    ')  # 所有换行符替换为4个空格
            clean_text = clean_text.translate(
                str.maketrans(":;()", "：；（）", "\'\"/\\")
            )  # 英文标点转中文标点，并删除斜杠、反斜杠、英文单双引号
            clean_text = clean_text.translate(
                str.maketrans("０１２３４５６７８９", "0123456789")
            )  # 中文全角数字转英文半角数字
            clean_text = settings.pattern_delete_bracket_contents.sub('', clean_text)  # 删除括号和括号里面的内容
        return clean_text  # str

    @property
    def without_puncs_text(self):
        """ 删除标点符号 """
        without_puncs_text = ''
        if self.clean_text:
            without_puncs_text = self.clean_text.translate(str.maketrans('', '', self.PUNCS))
        return without_puncs_text  # str

    def __money2num(self, money_str):
        """ 输入金额str（带'元'字），返回float（以万元为单位） """
        money_str = money_str.translate(str.maketrans({'余': None, '元': None, ',': None}))  # 消除'余元,'
        result = None
        # 参数检查
        if money_str.count('.') > 1:
            return result
        # 分类处理 纯汉字：一万三千(kind_tag=0) 或者 纯阿拉伯，阿拉伯数字+汉字：1.3万(kind_tag=1)
        kind_tag = 0
        for char in money_str:
            if char in self.NUMS:
                kind_tag = 1
                break
        # 纯汉字：一万三千
        if kind_tag == 0:
            res, tmp, hnd_mln = 0, 0, 0
            for curr_char in money_str:
                curr_digit = settings.MONEY_NUM_MAP[curr_char]
                # 处理亿
                if curr_digit == 10 ** 8:
                    res = res + tmp
                    res = res * curr_digit
                    hnd_mln = hnd_mln * 10 ** 8 + res
                    res = 0
                    tmp = 0
                # 处理万
                elif curr_digit == 10 ** 4:
                    res = res + tmp
                    res = res * curr_digit
                    tmp = 0
                # 处理千、百、十
                elif curr_digit >= 10:
                    tmp = 1 if tmp == 0 else tmp
                    res = res + curr_digit * tmp
                    tmp = 0
                # 处理单独数字
                else:
                    tmp = tmp * 10 + curr_digit
            res = res + tmp
            result = float(res + hnd_mln)
        # 阿拉伯数字+汉字：1.3万
        elif kind_tag == 1:
            if '万' in money_str:
                result = float(money_str[:-1]) * (10 ** 4)
            elif '亿' in money_str:
                result = float(money_str[:-1]) * (10 ** 8)
            else:
                result = float(money_str)
        result = result / 10000 if result else None
        return result  # float 以万元为单位

    def extract_moneys(self):
        """ 提取文本中的金额，返回含浮点数的元组或空元组。以万元为单位。 """
        moneys = []
        text = self.clean_text.replace('，', ',').replace('。', '.')  # 中文逗号、句号暂时全部转为英文
        money_strings = settings.pattern_money.findall(text)
        if money_strings:
            for m in money_strings:
                r = self.__money2num(m)
                if r is not None:
                    moneys.append(r)
        return tuple(moneys)  # tuple(float, )

    def extract_dates(self):
        """ 提取文本中的日期，形如XXXX年X月XX日，返回含datetime对象的元组或空元组 """
        dates = []
        date_strings = settings.pattern_date.findall(self.clean_text)
        if date_strings:
            for d in date_strings:
                try:
                    dates.append(datetime.strptime(d, '%Y年%m月%d日'))
                except ValueError:
                    pass
        return tuple(dates)  # tuple(datetime, )

    def check_exist(self, target):
        """ 判断目标字符串（含正则表达式）是否存在于text，返回None或第一个匹配的(开始索引，结束索引) """
        result = None
        match = re.search(target, self.clean_text)
        if match:
            result = match.span(0)
        return result  # tuple(int, int)

    @property
    def words(self):
        """ 分词和词性标注，返回一个含word对象（用 w.word 调用词，w.flag调用词性）的迭代器 """
        """ 常用标注集 n-名词 nr-人名 ns-地名 nt-团体名 nz-其他专词 """
        seg_list = pseg.cut(self.clean_text)
        return seg_list  # iterator

    @property
    def sentences(self):
        """ 将文本分割成句子，返回元组 """
        text_split = settings.pattern_sentences.split(self.clean_text)  # 不保留匹配项。 (正则式加上括号，可以保留匹配项)
        sentences = filter(lambda s: True if s else False, text_split)
        return tuple(sentences)  # tuple(str, )

    @staticmethod
    def period2num(period_string):
        """ 时长（类似X年X个月）转换成数字，以月份为单位 """
        recorder = 0
        for char in period_string:
            if char == '十':
                if recorder < 1:
                    recorder += 10
                else:
                    recorder = recorder * 10
            elif char in settings.PERIOD_NUM_DICT.keys():
                recorder += settings.PERIOD_NUM_DICT[char]
            elif char == '年':
                recorder *= 12
        result = recorder if recorder > 0 else None
        return result  # int


class ItemDumper:
    """ 要素输出的格式化。可同时格式化多个要素 """

    def __init__(self, *contents):
        self.contents = contents

    def __format_one(self, item):
        """ 格式化单个要素 """
        result = 'None'  # 默认输出'None'
        if item is None:
            result = 'None'  # None输出'None'
        elif isinstance(item, int):
            result = str(item)
        elif isinstance(item, float):
            result = '{:.2f}'.format(item)
        elif isinstance(item, str):
            result = item.replace(',', '')  # 对字符串，消除逗号
        elif isinstance(item, datetime):
            result = item.strftime('%Y-%m-%d')
        elif isinstance(item, (list, tuple)):
            result = '+'.join([self.__format_one(a) for a in item])
        return result

    def format(self):
        """ 单个输入返回单个，多个输入返回元组 """
        result = 'None'
        if len(self.contents) == 1:
            result = self.__format_one(self.contents[0])
        elif len(self.contents) > 1:
            result = tuple([self.__format_one(item) for item in self.contents])
        return result


class Csv:
    """ 上下文管理器 """
    """ 输出到csv文件 """

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.done_rows = 0

    def __enter__(self):
        self.f = open(self.csv_path, 'w', encoding='gbk')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()

    def export(self, **items):
        """ 输出一行到文件 """
        if self.done_rows == 0:  # 写入首行标签
            self.f.write(','.join(items.keys()))
            self.f.write("\n")

        self.f.write(','.join(map(lambda v: ItemDumper(v).format(), items.values())))
        self.f.write("\n")
        self.done_rows += 1
        print('export: {} rows done'.format(self.done_rows))


class Samples:
    """ 有放回的随机抽取人工抽检样本 """
    def __init__(self, universe, num):
        self.universe = universe  # 传入总体，列表或元组类型，元素为可用的paper_id
        self.length = len(universe)  # 总体的数量
        self.num = num  # 抽取样本的数量

    def choice(self):
        """ 抽取样本。num: 抽取的样本数量 """
        universe = np.array(self.universe, dtype='int32')  # 转化为整数类型的numpy数组
        result = np.random.choice(universe, self.num, replace=True)
        result = result.tolist()  # 转为普通列表
        return tuple(result)  # tuple(int, )

    def export_result(self, file_path):
        """ 输出抽取结果到文件，每行10个，制表符分隔 """
        """ 输出的同时，根据进度打印结果，每行10个 """
        result = self.choice()
        with open(file_path, 'w', encoding='utf-8') as f:
            for start_pos in range(0, len(result), 10):
                result_unit = result[start_pos: start_pos + 10]
                result_unit_str = "\t".join([str(paper_id) for paper_id in result_unit])
                f.write(result_unit_str)
                f.write("\n")
                print(result_unit_str)
        return 0


if __name__ == '__main__':
    pass

