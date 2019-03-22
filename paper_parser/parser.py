# -*- coding:utf-8


from paper_parser import functions
from paper_parser import settings
from paper_parser import models
from os import path


def paper_generator():
    """ 遍历文书对象 """
    with functions.MysqlConnector() as mc:
        select_sql = 'select {0} from {1} where id={{}}'.format(
            ','.join(settings.MysqlParameter.columns), settings.MysqlParameter.used_table
        )
        for row_id in range(1, mc.max_id + 1):
            if row_id in settings.MysqlParameter.skip_row_ids:
                continue
            mc.cursor.execute(select_sql.format(row_id))
            result = mc.cursor.fetchone()
            if not result:  # 不存在该id
                continue
            # 在此修改检索条件
            tag = result[settings.MysqlParameter.columns.index('tag')]
            if tag != 0:  # 非0表示该项数据不适用，或存在问题
                continue
            paper_content_encoded = result[settings.MysqlParameter.columns.index('paper_content')]
            paper_content_decoded = functions.PaperContentCoder.decode(paper_content_encoded)
            if not paper_content_decoded:  # json解码失败
                continue
            yield models.TanwuhuiluPaper(row_id, paper_content_decoded)


def paper_html_export(html_dir):
    """ 输出文书html。须指定输出的目录html_dir """
    if path.isdir(html_dir):
        for paper in paper_generator():
            file_name = '{}.html'.format(paper.paper_id)
            file_path = path.join(html_dir, file_name)
            paper.to_html(file_path)
    return 0


def paper_export(csv_path):
    """ 输出文书信息。须指定输出文件的路径csv_path """
    with functions.Csv(csv_path) as csv:
        for _paper in paper_generator():
            try:
                csv.export(
                    paper_id=_paper.paper_id,
                    paper_type=_paper.paper_type,
                    case_number=_paper.case_number,
                    cause=_paper.cause,
                    court=_paper.court,
                    court_level=_paper.court_level,
                    trial_level=_paper.trial_level,
                    province=_paper.province,
                    region=_paper.region,
                    city=_paper.city,
                    accept_date=_paper.accept_date,
                    judge_date=_paper.judge_date,
                    duration=_paper.duration,
                    chief_judge=_paper.chief_judge,
                    judges=_paper.judges,
                    jurors=_paper.jurors,
                    full_court=_paper.full_court,
                    clerk=_paper.clerk,
                    litigants=_paper.litigants,
                    lawyers=_paper.lawyers,
                    lawyer_firms=_paper.lawyer_firms,
                    is_delayed=_paper.is_delayed,
                    is_designated=_paper.is_designated,
                    is_simple_procedure=_paper.is_simple_procedure,
                    prosecution=_paper.prosecution,
                    crime_law_version=_paper.crime_law_version,
                    prosecutors=_paper.prosecutors,
                    prosecute_number=_paper.prosecute_number,
                    defendant_name=_paper.defendant_info['name'],
                    defendant_is_name_covered=_paper.defendant_info['is_name_covered'],
                    defendant_sex=_paper.defendant_info['sex'],
                    defendant_birth=_paper.defendant_info['birth'],
                    defendant_age=_paper.defendant_info['age'],
                    defendant_tribe=_paper.defendant_info['tribe'],
                    defendant_is_minor=_paper.defendant_info['is_minor'],
                    defendant_educated=_paper.defendant_info['educated'],
                    defendant_job=_paper.defendant_info['job'],
                    is_plus_investigated=_paper.is_plus_investigated,
                    is_defensive_opinions_accepted=_paper.is_defensive_opinions_accepted,
                    is_leifan=_paper.is_leifan,
                    is_ligong=_paper.is_ligong,
                    is_zishou=_paper.is_zishou,
                    is_tanbai=_paper.is_tanbai,
                    amounts_unsure=_paper.amounts['unsure'],
                    amounts_sure=_paper.amounts['sure'],
                    num_of_facts=_paper.num_of_facts,
                    job=_paper.job_info['job'],
                    job_type=_paper.job_info['job_type'],
                    job_grade=_paper.job_info['job_grade'],
                    penalty_many=_paper.penalty['many'],
                    penalty_freedom=_paper.penalty['freedom'],
                    penalty_property=_paper.penalty['property'],
                    penalty_right=_paper.penalty['right'],
                    penalty_delay=_paper.penalty['delay']
                )
            except UnicodeEncodeError:
                pass


def get_samples(file_path, num=385):
    """ 获取重复抽样样本的paper_id。必须指定输出文件的路径；可指定抽样数量，默认为385 """
    # 获取抽样样本
    paper_ids = []
    print('Creating paper_ids Samples...')
    for paper in paper_generator():
        paper_ids.append(paper.paper_id)
        if paper.paper_id % 10 == 0:  # 进度显示，以10为单位
            print(paper.paper_id)
    print('Created paper_ids Samples')
    functions.Samples(paper_ids, num).export_result(file_path)
    return 0


if __name__ == '__main__':
    pass

    # paper_html_export('F//')
    # paper_export('F//.csv')
    # get_samples('F//.txt')
