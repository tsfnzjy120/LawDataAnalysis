# -*- coding:utf-8 -*-


import re


# Mysql参数
class MysqlParameter:

    host, port, charset = '127.0.0.1', 3306, 'utf8'
    users, passwds = ('user1', 'passwd1'), ('user2', 'passwd2')
    database = 'db_name'
    tables = ('table_name', )
    used_table = tables[0]  # 根据使用的表修改
    columns = (
        'id', 'jid', 'case_num', 'title', 'judge_date', 'province', 'court',
        'cause', 'trial_level', 'paper_type', 'paper_content', 'tag'
    )
    skip_row_ids = ()


PROVINCE_DICT = {
    '北京': 11, '天津': 12, '河北': 13, '山西': 14, '内蒙古': 15,
    '辽宁': 21, '吉林': 22, '黑龙江': 23,
    '上海': 31, '江苏': 32, '浙江': 33, '安徽': 34, '福建': 35, '江西': 36, '山东': 37,
    '河南': 41, '湖北': 42, '湖南': 43, '广东': 44, '广西': 45, '海南': 46,
    '重庆': 50, '四川': 51, '贵州': 52, '云南': 53, '西藏': 54,
    '陕西': 61, '甘肃': 62, '青海': 63, '宁夏': 64, '新疆': 65
}
EDUCATED_DICT = {
    '小学': 1, '初中': 2, '高中': 3, '中专': 3, '大专': 4, '专科': 4, '大学': 5, '本科': 5, '研究生': 6
}
MONEY_NUM_MAP = {
    # 数字
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '壹': 1, '两': 2, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    # 单位
    '十': 10, '百': 10 ** 2, '千': 10 ** 3, '万': 10 ** 4, '亿': 10 ** 8, '拾': 10, '佰': 10 ** 2, '仟': 10 ** 3,
}
PERIOD_NUM_DICT = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
}


# 正则表达式
pattern_money = re.compile(r'\d[0-9,.]*[万亿]?余?元|[零一壹二两贰三叁四肆五伍六陆七柒八捌九玖十拾百佰千仟万亿]+余?元')
pattern_date = re.compile(r'\d{4}年\d{1,2}月\d{1,2}日')
pattern_delete_bracket_contents = re.compile(r'（.*?）')
pattern_sentences = re.compile(r'[。！？]')
pattern_crime_law_version = re.compile(r'刑法（(\d{4})修正）')
pattern_prosecutors = re.compile(r'指派(.+?)出庭')
pattern_prosecutors_delete_strings = re.compile(r'(?:副|助理|代理)?检察[长官员](助理)?|书记员')
pattern_prosecute_number = re.compile(r'院以(.+?)起诉书')
pattern_is_delayed = re.compile(r'延[长期]审理')
pattern_defendant = {
    'name': re.compile(r'被告人?(.+?)，'), 'birth': re.compile(r'\d{4}年\d{1,2}月\d{1,2}日出?生|生于\d{4}年\d{1,2}月\d{1,2}日'),
    'age': re.compile(r'(\d{2})岁'), 'tribe': re.compile('，([\u4e00-\u9fff]+?族)[，。]'),
    'educated': (re.compile(r'，([\u4e00-\u9fff]+?)文化'), re.compile(r'文化程度([\u4e00-\u9fff]+?)[，。]', )),
    'job': re.compile(r'(?<![主责])[任系原]+([\u4e00-\u9fff].+?)[，。、]')
}
pattern_inaccurate_amounts = re.compile(r'[数金]额[^罪名]*?不准')
pattern_tanbai = re.compile(r'坦白|认罪|如实供述|配合')
pattern_period = re.compile(r'[\u4e00-\u9fff]([一二两三四五六七八九十]{1,2}年?又?[一二两三四五六七八九十]*个?月?)[^\u4e00-\u9fff]')
pattern_penalty = {
    'many': re.compile(r'犯[\u4e00-\u9fff、]+?罪'),
    'split': re.compile(r'犯[\u4e00-\u9fff]+?罪|执行'),
    'freedom': {
        'juyi': re.compile(r'拘役([一二两三四五六七八九十]{1,2}年?又?零?[一二两三四五六七八九十]*个?月?)'),
        'youqitx': re.compile(r'有期徒刑([一二两三四五六七八九十]{1,2}年?又?零?[一二两三四五六七八九十]*个?月?)'),
        'wuqitx': re.compile(r'无期徒刑'),
        'sixing': re.compile(r'死刑')
        # 暂时缺少管制刑
    },
    'property': {
        'fajin': re.compile(r'罚金[人民币]*([0-9,.零一壹二贰两三叁四肆五伍六陆七柒八捌九玖十拾百佰千仟万亿]+元)'),
        'moshou': re.compile(r'财产[人民币]*([0-9,.零一壹二贰两三叁四肆五伍六陆七柒八捌九玖十拾百佰千仟万亿]+元)')
    },
    'right': re.compile(r'政治权利([一二两三四五六七八九十]{1,2}年?又?零?[一二两三四五六七八九十]*个?月?)'),
    'delay': re.compile(r'缓[刑期]考?验?期?([一二两三四五六七八九十]{1,2}年?又?零?[一二两三四五六七八九十]*个?月?)'),
    'free': re.compile(r'免[予于除]|无罪')
}
pattern_num_of_facts = re.compile(r'(\d{4})年([0-9春夏秋冬]{0,2})')
pattern_job_info = {
    'job': re.compile(r'任([^某何免务用凭教由职能的、，。； ][\u4e00-\u9fff0-9a-zA-Z]+?)[期以时的职、，。； ]'),
    'job_type': None,
    'job_grade': None
}
# html template
html_template_head = """<!DOCTYPE html>
<html><head>
<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />
<title>{title}</title>
<style type=\"text/css\">
body {
    font-family: \"Microsoft YaHei\";
    font-size: 1.5rem;
    background-color: #A0EEE1;
}
</style>
</head>
<body>
"""
html_template_tail = """
<p>中国人民大学未来法治研究院数据法学实验室制</p>
<p>tsfnzjy120@ruc.edu.cn</p>
</body>
</html>
"""


