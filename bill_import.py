import pandas as pd
import sys
import os
import re

pd.options.mode.chained_assignment = None  # default='warn'

# classification.csv和脚本文件放在一起
reader = pd.read_csv(r"./classification.csv", encoding='gbk', sep=',')
patt = re.compile(r"1[34578]\d{9}(?:充值|缴费|交费)")


# 根据txt的文本判断账单分类
def classify_by_csv(txt):
    for index, rows in reader.iteritems():
        for row in rows:
            if isinstance(row, str) and row.__len__() > 0 and row in txt:
                return index
            elif patt.search(txt):
                return "通讯物流"
    return '其它'


def convert_from_alipay(filename):
    print(f"---------alipay: {filename} ---------")
    try:
        df = pd.read_csv(os.path.realpath(filename), skiprows=4, encoding='gbk')
        # 对每个元素strip
        df = df.astype(str).applymap(lambda x: x.strip())
        # 列名strip
        df = df.rename(columns={x: x.strip() for x in df.columns.to_list()})
        # 包含成功的交易状态
        succ_df = df[(df['交易状态'].str.contains('成功')) & (df['收/支'] != '')]
        succ_df["备注"] = succ_df.apply(lambda x: "|-|".join([x['交易对方'], x['商品名称'], x['交易来源地']]), axis=1)
        succ_df["分类"] = None
        # 新建excel
        out_df = succ_df[['交易创建时间', '分类', '收/支', '金额（元）', '备注']]
        # 重命名
        out_df = out_df.rename(columns={"交易创建时间": "时间", "收/支": "收入或支出", "金额（元）": "金额"})
        return out_df
    except Exception as e:
        print(e)


def convert_from_wechat_pay(filepath_argv):
    print(f"---------wechat: {filepath_argv} ---------")
    try:
        # 编码格式为UTF8-BOM
        df = pd.read_csv(filepath_argv, skiprows=16, encoding='utf-8-sig', sep=',')
        df['备注'] = df.apply(lambda x: "|-|".join([x['交易对方'], x['商品'], x['交易类型']]), axis=1)
        succ_df = df[df['收/支'] != '']
        succ_df["分类"] = None
        out_df = succ_df[['交易时间', '分类', '收/支', '金额(元)', '备注']]
        out_df = out_df.rename(columns={"交易时间": "时间", "收/支": "收入或支出", "金额(元)": "金额"})
        out_df['金额'] = out_df['金额'].map(lambda x: x[1:])

        return out_df
    except Exception as e:
        print(e)


def help_and_exit():
    print("Usage :python bill_import.py csv_dirname")
    sys.exit(-1)


if __name__ == "__main__":
    # print(classify_by_csv("鱼小喵在成都(时代天街店)外卖订单"))
    if sys.argv.__len__() != 2:
        help_and_exit()
    bill_dir = os.path.abspath(sys.argv[1])
    csv_files = [os.path.join(bill_dir, x) for x in os.listdir(bill_dir) if
                 x.endswith(".csv") and 'classification' not in x]
    for csv in csv_files:
        bill_filename = os.path.realpath(csv)
        if "alipay" in bill_filename:
            converted_df = convert_from_alipay(bill_filename)
        elif "微信支付账单" in bill_filename:
            converted_df = convert_from_wechat_pay(bill_filename)
        else:
            print(f"can not handle {csv}")
            continue

        assert converted_df is not None, f"df from {bill_filename} is None!"

        converted_df['分类'] = converted_df['备注'].map(classify_by_csv)
        path = os.path.splitext(bill_filename)[0]
        converted_df.to_excel(path + ".xls", index=None, encoding='utf-8')
        print(f"File saved to {path}.xls successfully.")
