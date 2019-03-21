# -*- coding:utf-8 -*-


import ujson
from paper_parser import settings
from paper_parser import functions
from datetime import datetime
import os


class Paper:
    """ 文书基类 """

    # 接收id和json字符串
    def __init__(self, row_id, paper_content):
        self.paper_id = row_id  # int
        self.paper_content = paper_content  # str

    @property
    def json(self):
        json = ujson.loads(self.paper_content)
        return json

    # 以下皆可能返回None
    @property
    def jid(self):
        """ 获取文书jid """
        jid = self.json['jid'].upper()
        return jid  # str

    @property
    def paper_type(self):
        """ 获取文书类型 1-判决书 """
        paper_type = self.json['type']
        return paper_type  # int

    @property
    def case_number(self):
        """ 获取案号 """
        case_number = self.json['all_caseinfo_casenumber']
        return case_number  # str

    @property
    def title(self):
        """ 获取案件名 """
        title = self.json['all_caseinfo_casename']
        return title  # str

    @property
    def cause_tree(self):
        """ 获取案由树，返回六元组，0-树的深度 1-1级案由 2-2级案由... """
        cause_tree = [
            self.json['level1_case'], self.json['level2_case'], self.json['level3_case'],
            self.json['level4_case'], self.json['level5_case'],
        ]
        tree_depth = 5 - cause_tree.count(None)
        cause_tree.insert(0, tree_depth)
        return tuple(cause_tree)  # tuple(int, str, str, str, None, None)

    @property
    def cause(self):
        """ 获取案由 """
        cause = self.json['all_text_cause']
        return cause  # str

    @property
    def court(self):
        """ 获取法院名 """
        court = self.json['all_caseinfo_court']
        return court  # str

    @property
    def court_level(self):
        """ 获取法院级别 1-基层 2-中级 3-高级 4-最高 9-其他 """
        court_level_string = self.json['court_level']
        court_level = None
        if court_level_string:
            if '基层' in court_level_string:
                court_level = 1
            elif '中级' in court_level_string:
                court_level = 2
            elif '高级' in court_level_string:
                court_level = 3
            elif '最高' in court_level_string:
                court_level = 4
            else:
                court_level = 9
        return court_level  # int

    @property
    def trial_level(self):
        """ 获取审理级别 1-一审 """
        trial_level = self.json['all_caseinfo_leveloftria']
        return trial_level  # int

    @property
    def province(self):
        """ 获取省份，用行政代码表示。默认值是None """
        province_string = self.json['province']
        province_id = None
        if province_string:
            for province in settings.PROVINCE_DICT.keys():
                if province in province_string:
                    province_id = settings.PROVINCE_DICT[province]
                    break
        return province_id  # int

    @property
    def region(self):
        """ 获取地区，包含省份 """
        province = self.json['province']
        region_later = self.json['region']  # region的后半部分
        region = None
        if region_later:
            region = province + region_later if province else region_later
        return region  # str

    @property
    def city(self):
        """ 获取城市，包含省份 """
        province = self.json['province']
        city_later = self.json['city']  # city的后半部分
        city = None
        if city_later:
            city = province + city_later if province else city_later
        return city  # str

    @property
    def accept_date(self):
        """ 获取受理日期 """
        accept_date_string = self.json['accept_date']
        accept_date = None
        if accept_date_string:
            accept_date = datetime.strptime(accept_date_string, "%Y-%m-%d")
        return accept_date  # datetime类

    @property
    def judge_date(self):
        """ 获取结案日期 """
        judge_date_string = self.json['all_judgementinfo_date']
        judge_date = None
        if judge_date_string:
            judge_date = datetime.strptime(judge_date_string, "%Y-%m-%d")
        return judge_date  # datetime类

    @property
    def duration(self):
        """ 获取审理时长，按天数计 """
        time_delta = None
        if self.judge_date and self.accept_date:
            time_delta = (self.judge_date - self.accept_date).days
        return time_delta  # int

    @property
    def chief_judge(self):
        """ 获取主审法官 """
        chief_judge = self.json['all_chief_judge']
        return chief_judge  # str

    @property
    def judges(self):
        """ 获取法官列表，包含主审法官，不含陪审员 """
        judges = self.json['all_judges']
        return judges  # list[str, ]

    @property
    def jurors(self):
        """ 获取陪审员列表 """
        jurors_string = self.json['all_people_jury']
        jurors = []
        if jurors_string:
            jurors.extend(jurors_string.split(';'))
        return jurors  # list[str, ]

    @property
    def full_court(self):
        """ 根据审理人数，判断是否合议庭 0-否 1-是 默认1 """
        full_court = 1
        if self.judges:
            if len(self.judges) == 1 and self.jurors is not None and len(self.jurors) == 0:
                full_court = 0
        return full_court

    @property
    def clerk(self):
        """ 获取书记员姓名 """
        clerk = self.json['all_clerk']
        return clerk  # str

    @property
    def litigants(self):
        """ 获取当事人列表 """
        litigants = self.json['all_litigant']
        return litigants  # list[str, ]

    @property
    def law_articles(self):
        """ 获取适用法律信息，返回包含二元组(法律名，法条名)的列表 """
        law_articles_detail = self.json['law_regu_details']
        law_articles = []
        if law_articles_detail:
            for law_article_dict in law_articles_detail:
                law_articles.append((law_article_dict["lawName"], law_article_dict["tiaoName"]))
        return law_articles  # list[(str, str), ]

    @property
    def all_text(self):
        """ 获取文书全文 """
        paragraphs = self.json['paragraphs']
        all_text = ''
        if paragraphs:
            for para in paragraphs:
                if para['text']:
                    all_text += para['text']
        return all_text  # str

    @property
    def all_paragraphs(self):
        """ 获取文书所有段落，返回包含四元组(标签类型，标签名，段落长度，段落)的迭代器 """
        """ (一审) 0-正文 1-当事人信息 2-案件概述 6-一审法院查明 7-一审法院认为 8-一审裁判结果 9-审判人员 10-裁判附件 """
        paragraphs = self.json['paragraphs']
        if paragraphs:
            for para in paragraphs:
                yield para['labelType'], para['lableName'], para['length'], para['text']  # (int, str, int, str)

    @property
    def all_sentences(self):
        """ 获取文书所有句子，返回包含三元组(所在段落的标签类型，句子长度，句子)的迭代器 """
        paragraphs = self.json['paragraphs']
        if paragraphs:
            for para in paragraphs:
                sub_paragraphs = para['subParagraphs']
                if sub_paragraphs:
                    for sub_para in sub_paragraphs:
                        sentences = sub_para['sentences']
                        if sentences:
                            for sent in sentences:
                                yield para['labelType'], sent['length'], sent['text']  # (int, int, str)

    def to_html(self, html_path):
        """ 输出文书内容到html文件。必须指定绝对路径html_path """
        """ 按段落输出，同时输出各段落标记 """
        file_name = '{}.html'.format(self.paper_id)
        if os.path.isdir(html_path):
            file_path = os.path.join(html_path, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(settings.html_template_head.replace('{title}', str(self.paper_id)))
                jid, cause, title, case_number, court = functions.ItemDumper(  # 格式化输出
                    self.jid, self.cause, self.title, self.case_number, self.court
                ).format()
                f.write("""<p>{0} {1}</p>\n<p>{2}</p>\n<p>{3}</p>\n<p>{4}</p>\n""".format(jid, cause, title, case_number, court))
                for para in self.all_paragraphs:
                    f.write("<p>{0}.{1}</p>\n<p>{2}</p>\n".format(
                        para[0], para[1], functions.TextProcessor(para[3]).clean_text
                    ))
                f.write(settings.html_template_tail)
            print('to html file finished: {}'.format(file_path))
        return 0


class JudgePaper(Paper):
    """ 判决书类 paper_type = 1 """

    # 以下适用一审、二审、再审
    @property
    def lawyers(self):
        """ 获取律师信息，返回列表 """
        lawyers = self.json['lawyer_term']
        return lawyers  # list[str, ]

    @property
    def lawyer_firms(self):
        """ 获取律所信息，返回列表 """
        lawyer_firms = self.json['lawfirm_term']
        return lawyer_firms  # list[str, ]

    @property
    def litigant_info_text(self):
        """ 含各诉讼当事人基本信息的文本段 """
        litigant_info_text = self.json['all_text_litigantinfo']
        return litigant_info_text  # str

    @property
    def evidence_text(self):
        """ 含证据清单的文本 """
        evidence_text = self.json['evidence']
        return evidence_text  # str

    @property
    def attachment_text(self):
        """ 附件文本 """
        attachment_text = None
        for para in self.all_paragraphs:
            if para[0] == 10:
                attachment_text = para[3]
        return attachment_text

    # 以下暂时只适用一审
    @property
    def is_delayed(self):
        """ 是否延期 0-否 1-是 默认0 """
        is_delayed = 0
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_basic_text).clean_text
            match = settings.pattern_is_delayed.search(text)
            if match:
                is_delayed = 1

        return is_delayed

    # 以下暂时只适用二审

    # 以下暂时只适用再审

    # 以下仅适用一审
    @property
    def first_basic_text(self):
        """ 获取一审案件基本信息 """
        first_basic_text = self.json["firstinstance_text_basicinfo"]
        return first_basic_text  # str

    @property
    def first_fact_text(self):
        """ 获取一审案件事实：经审理查明 """
        first_fact_text = self.json['firstinstance_text_fact']
        return first_fact_text  # str

    @property
    def first_opinion_text(self):
        """ 获取一审案件法院意见：本院认为 """
        first_opinion_text = self.json['firstinstance_text_opinion']
        return first_opinion_text  # str

    @property
    def first_judge_text(self):
        """ 获取一审案件判决结果：判决如下 """
        first_judge_text = self.json['firstinstance_text_judgement']
        return first_judge_text  # str

    @property
    def is_designated(self):
        """ 是否指定管辖 0-否 1-是 默认0"""
        is_designated = 0
        if '管辖' in functions.TextProcessor(self.first_basic_text).clean_text:
            is_designated = 1
        return is_designated

    @property
    def is_simple_procedure(self):
        """ 是否简易程序 0-否 1-是 默认0 """
        is_simple_procedure = 0
        text = functions.TextProcessor(self.first_basic_text).clean_text
        if '简易程序' in text and '转为普通程序' not in text:
            is_simple_procedure = 1
        return is_simple_procedure

    # 以下仅适用二审

    # 以下仅适用再审


class CivilJudgePaper(JudgePaper):
    """ 民事判决书类 cause_tree[1] = '民事' """

    @property
    def accept_fee(self):
        """ 获取诉讼费 """
        accept_fee = int(self.json['acceptance_fee'])
        return accept_fee  # int


class CrimeJudgePaper(JudgePaper):
    """ 刑事判决书类 cause_tree[1] = '刑事' """

    @property
    def prosecution(self):
        """ 获取公诉机关 """
        prosecution = self.json['prosecution_organ_term']
        if prosecution:
            prosecution = prosecution[0]
        return prosecution  # str

    @property
    def crime_law_version(self):
        """ 判断所适用的刑法的版本，用修正时的年份表示。返回int """
        crime_law_version = None
        for law, article in self.law_articles:
            match = settings.pattern_crime_law_version.search(law)
            if match:
                crime_law_version = int(match.group(1))
                break
        return crime_law_version  # int

    # 以下暂时仅适用一审
    @property
    def prosecutors(self):
        """ 获取公诉人姓名列表 """
        prosecutors = []
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_basic_text).clean_text
            match = settings.pattern_prosecutors.search(text)
            if match:
                prosecutors = list(map(lambda a: settings.pattern_prosecutors_delete_strings.sub('', a), match.group(1).split('、')))

        return prosecutors  # list[str, ]

    @property
    def prosecute_number(self):
        """ 获取起诉书号 """
        prosecute_number = None
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_basic_text).clean_text
            match = settings.pattern_prosecute_number.search(text)
            if match:
                prosecute_number = match.group(1)

        return prosecute_number  # str

    @property
    def defendant_info(self):
        """ 获取被告人信息字典 """
        text = functions.TextProcessor(self.litigant_info_text).clean_text
        defendant_info = {
            'name': None, 'is_name_covered': None, 'sex': 1, 'birth': None, 'age': None,
            'tribe': '汉族', 'is_minor': 0, 'educated': None, 'job': None
        }
        if text:
            if self.trial_level == 1:
                # 获取更准确的含被告人信息的句子
                text_split = text.split('    ')
                if len(text_split) < 2:
                    return defendant_info  # 无法正确获得含被告人信息的句子
                defendant_text = text_split[1][:text_split[1].find('。')] + '。'
                # name, is_name_covered
                name_match = settings.pattern_defendant['name'].search(defendant_text)
                if name_match:
                    name = name_match.group(1)
                    defendant_info['name'] = name if len(name) < 10 else None
                if defendant_info['name']:
                    if '某' in defendant_info['name'] or functions.TextProcessor(defendant_info['name']).check_exist(r'[^\u4e00-\u9fff]'):
                        defendant_info['is_name_covered'] = 1
                    else:
                        defendant_info['is_name_covered'] = 0
                else:
                    return defendant_info  # 如果找不到姓名，则视为句子有缺陷，不再继续查找其他被告人信息，直接返回默认字典
                # sex
                if '，女' in defendant_text:
                    defendant_info['sex'] = 0
                # birth, age
                birth_match = settings.pattern_defendant['birth'].search(defendant_text)
                if birth_match:
                    defendant_info['birth'] = functions.TextProcessor(birth_match.group(0)).extract_dates()[0]
                    defendant_info['age'] = self.judge_date.year - defendant_info['birth'].year if self.judge_date else None
                if not defendant_info['age']:  # 有些判决书直接写了年龄
                    age_match = settings.pattern_defendant['age'].search(defendant_text)
                    if age_match:
                        defendant_info['age'] = int(age_match.group(1))
                # tribe, is_minor
                tribe_match = settings.pattern_defendant['tribe'].search(defendant_text)
                if tribe_match:
                    defendant_info['tribe'] = tribe_match.group(1)
                    if defendant_info['tribe'] != '汉族':
                        defendant_info['is_minor'] = 1
                # educated 1-小学 2-初中 3-高中、中专 4-大专、专科 5-大学、本科 6-研究生
                educated_name = None
                for pattern_educated in settings.pattern_defendant['educated']:
                    educated_match = pattern_educated.search(defendant_text)
                    if educated_match:
                        educated_name = educated_match.group(1)
                        break
                if educated_name:
                    for e_key in settings.EDUCATED_DICT.keys():
                        if e_key in educated_name:
                            defendant_info['educated'] = settings.EDUCATED_DICT[e_key]
                            break
                # job
                job_match = settings.pattern_defendant['job'].search(defendant_text)  # 先在defendant_text中找
                if job_match:
                    defendant_info['job'] = job_match.group(1)

        return defendant_info  # dict

    @property
    def is_plus_investigated(self):
        """ 是否有补充侦查 0-否 1-是 默认0 """
        is_plus_investigated = 0
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_basic_text).clean_text
            if '补充侦查' in text:
                is_plus_investigated = 1

        return is_plus_investigated  # int

    @property
    def defensive_opinions(self):
        """ 在法院认定意见中，获取含辩护意见的多个句子元组或空元组 """
        defensive_opinions = []
        if self.trial_level == 1:
            opinion_sentences = functions.TextProcessor(self.first_opinion_text).sentences
            if opinion_sentences:
                if '本院认为' in opinion_sentences[0]:
                    for s in opinion_sentences:
                        if '辩护' in s:
                            defensive_opinions.append(s)
        return tuple(defensive_opinions)  # tuple(str, )

    @property
    def is_defensive_opinions_accepted(self):
        """ 辩护意见是否被采信 0-不采信 1-部分采信 2-全部采信 """
        is_defensive_opinions_accepted = None
        sentences_accepted = []
        for sentence in self.defensive_opinions:
            if '予以' in sentence:
                if '不予' in sentence:
                    is_defensive_opinions_accepted = 1
                    break
                else:
                    sentences_accepted.append('予以')
            else:
                if '不予' in sentence:
                    sentences_accepted.append('不予')
        if len(sentences_accepted) > 0:
            if '予以' in sentences_accepted:
                if '不予' in sentences_accepted:
                    is_defensive_opinions_accepted = 1
                else:
                    is_defensive_opinions_accepted = 2
            else:
                if '不予' in sentences_accepted:
                    is_defensive_opinions_accepted = 0
        return is_defensive_opinions_accepted

    @property
    def is_leifan(self):
        """ 是否累犯 0-否 1-是 默认0 """
        is_leifan = 0
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_opinion_text).clean_text
            # 消除辩护意见
            for sentence in self.defensive_opinions:
                text = text.replace(sentence, '')
            if '累犯' in text:
                is_leifan = 1

        return is_leifan

    @property
    def is_ligong(self):
        """ 是否有立功情节 0-否 1-是 默认0 """
        is_ligong = 0
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_opinion_text).clean_text
            # 消除辩护意见
            for sentence in self.defensive_opinions:
                text = text.replace(sentence, '')
            if '立功' in text:
                is_ligong = 1

        return is_ligong

    @property
    def is_zishou(self):
        """ 是否有自首情节 0-否 1-是 默认0 """
        is_zishou = 0
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_opinion_text).clean_text
            # 消除辩护意见
            for sentence in self.defensive_opinions:
                text = text.replace(sentence, '')
            if '自首' in text:
                is_zishou = 1

        return is_zishou

    @property
    def is_tanbai(self):
        """ 是否有坦白情节 0-否 1-是 默认0 """
        """ 包含四种表述：坦白；认罪；如实供述；配合 """
        is_tanbai = 0
        if self.is_zishou:  # 是自首的一定是坦白
            is_tanbai = 1
        elif self.trial_level == 1:
            text = functions.TextProcessor(self.first_opinion_text).clean_text
            # 消除辩护意见
            for sentence in self.defensive_opinions:
                text = text.replace(sentence, '')
            tanbai_match = settings.pattern_tanbai.search(text)
            if tanbai_match:
                is_tanbai = 1

        return is_tanbai

    @property
    def penalty(self):
        """ 判决结果 """
        penalty = None
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_judge_text).clean_text.split('    ')[0]
            penalty = {'many': None, 'freedom': None, 'property': None, 'right': None, 'delay': None}
            # many 确定罪数
            many_strings = settings.pattern_penalty['many'].findall(text)
            if many_strings:  # 如果提取不到罪数，则认为该句存在问题，放弃继续提取；如有罪数，则改其他项的None为0
                penalty = {'many': len(many_strings), 'freedom': 0, 'property': 0.0, 'right': 0, 'delay': 0}
                text = settings.pattern_penalty['split'].split(text)[-1]  # 定位最终执行语句
                # freedom  主刑
                for k, v in settings.pattern_penalty['freedom'].items():
                    freedom_match = v.search(text)
                    if freedom_match:
                        if k == 'juyi':  # 拘役用负数表示
                            penalty['freedom'] = -functions.TextProcessor.period2num(freedom_match.group(1))
                        elif k == 'youqitx':  # 有期徒刑用正数表示
                            penalty['freedom'] = functions.TextProcessor.period2num(freedom_match.group(1))
                        elif k in ('wuqitx', 'sixing'):  # 无期徒刑、死刑直接写入
                            penalty['freedom'] = freedom_match.group(0)
                        break
                # property  财产刑
                if '全部' in text:  # 先搜索没收个人全部财产，如有，直接写入字符串
                    penalty['property'] = '全部'
                else:
                    fajin_match = settings.pattern_penalty['property']['fajin'].search(text)
                    moshou_match = settings.pattern_penalty['property']['moshou'].search(text)
                    fajin_money = functions.TextProcessor(fajin_match.group(1)).extract_moneys() if fajin_match else None
                    moshou_money = functions.TextProcessor(moshou_match.group(1)).extract_moneys() if moshou_match else None
                    if fajin_money and moshou_money:  # 同时有罚金和没收，合并数额，在前面冠以±号
                        penalty['property'] = '±{0:.2f}'.format(fajin_money[0] + moshou_money[0])
                    elif fajin_money:  # 只有罚金，用正值表示
                        penalty['property'] = fajin_money[0]
                    elif moshou_money:  # 只有没收，用负值表示
                        penalty['property'] = -moshou_money[0]
                # right  资格刑
                if '政治权利终身' in text:  # 先搜索剥夺政治权利终身，如有，直接写入字符串
                    penalty['right'] = '终身'
                else:  # 搜索剥夺政治权利的具体时长
                    right_match = settings.pattern_penalty['right'].search(text)
                    if right_match:
                        penalty['right'] = functions.TextProcessor.period2num(right_match.group(1))
                # delay  缓刑
                delay_match = settings.pattern_penalty['delay'].search(text)
                if delay_match:
                    penalty['delay'] = functions.TextProcessor.period2num(delay_match.group(1))
                # free 检查是否免予处罚、无罪
                free_match = settings.pattern_penalty['free'].search(text)
                if free_match:  # 重置为0
                    penalty = {'many': penalty['many'], 'freedom': 0, 'property': 0.0, 'right': 0, 'delay': 0}

        return penalty


class TanwuhuiluPaper(CrimeJudgePaper):
    """ 贪污贿赂罪刑事判决书类 cause_tree[2] = '贪污贿赂罪' """

    # 以下暂时只针对一审
    @property
    def __amount_unsure(self):
        """ 根据案件概述，初步获得起诉的总金额 """
        amount_unsure = None
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_basic_text).clean_text
            moneys = functions.TextProcessor(text).extract_moneys()
            if moneys:
                amount_unsure = max(moneys)

        return amount_unsure  # float, 以万元为单位

    @property
    def __amount_sure(self):
        """ 根据法院认定情况或已查明的事实，初步获得认定的总金额 """
        amount_sure = None
        if self.trial_level == 1:
            # 首先在法院认定情况中寻找
            text = functions.TextProcessor(self.first_opinion_text).clean_text
            moneys = functions.TextProcessor(text).extract_moneys()
            if moneys:
                amount_sure = max(moneys)
            # 如果找不到，再在已查明的事实中寻找
            if amount_sure is None:
                text = functions.TextProcessor(self.first_fact_text).clean_text
                moneys = functions.TextProcessor(text).extract_moneys()
                if moneys:
                    amount_sure = max(moneys)
        return amount_sure  # float, 以万元为单位

    @property
    def amounts(self):
        """ 获取涉案金额，返回字典 """
        amount_unsure, amount_sure = self.__amount_unsure, self.__amount_sure
        amounts = {'unsure': amount_unsure, 'sure': amount_sure}
        if amount_unsure is not None:
            if amount_sure is not None:
                if amount_unsure < amount_sure:  # 如果认定的金额大于起诉的金额
                    text = functions.TextProcessor(self.first_opinion_text).clean_text
                    inaccurate_amounts_match = settings.pattern_inaccurate_amounts.search(text)
                    if inaccurate_amounts_match:  # 起诉金额不准确
                        amounts['sure'] = amount_unsure - 0.01  # 认定金额 = 起诉金额 - 100
                    else:  # 起诉金额准确
                        amounts['sure'] = amount_unsure  # 认定金额 = 起诉金额
            else:
                amounts['sure'] = amount_unsure  # 如果认定的金额不存在，则将起诉的金额用于认定的金额
        return amounts  # dict{float, }

    @property
    def num_of_facts(self):
        """ 犯罪事实的数量。根据日期的数量综合判断 """
        num_of_facts = None
        if self.trial_level == 1:
            text = functions.TextProcessor(self.first_fact_text).clean_text
            fact_date_ints = []
            all_match = settings.pattern_num_of_facts.finditer(text)
            for match in all_match:
                year_str = match.group(1)
                month_str = match.group(2).translate(str.maketrans({'春': '3', '夏': '6', '秋': '9', '冬': '12'}))
                fact_date_int = int(year_str) * 100 + int(month_str) if month_str else int(year_str) * 100  # 将日期格式化为六位数的int
                fact_date_ints.append(fact_date_int)
            fact_date_ints = sorted(list(set(fact_date_ints)))  # 去重、排序
            if len(fact_date_ints) == 1:
                num_of_facts = 1
            elif len(fact_date_ints) > 1:
                num_of_facts = len(fact_date_ints) - 1

        return num_of_facts

    @property
    def job_info(self):
        """ 犯罪行为人或犯罪对象的职务信息，包括职务名、单位性质、职务级别。该字段在paper.defendant_info['job']的基础上针对贪污贿赂罪拓展 """
        job_info = {'job': None, 'job_type': None, 'job_grade': None}
        if self.trial_level == 1:
            # 寻找职务名
            if self.defendant_info['job'] is not None:  # 直接引用paper.defendant_info['job']
                job_info['job'] = self.defendant_info['job']
            else:
                first_fact_text_split = functions.TextProcessor(self.first_fact_text).clean_text.split('：')
                text = first_fact_text_split[1] if len(first_fact_text_split) > 1 else first_fact_text_split[0]
                job_match = settings.pattern_job_info['job'].search(text)
                if job_match:
                    job_info['job'] = job_match.group(1)

        return job_info



if __name__ == '__main__':
    pass