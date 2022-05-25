import requests 
from datetime import date,datetime
import re 
import os
from lxml import etree
import jieba
import collections
import pyecharts.options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.charts import Bar3D,Line,Scatter,Pie,Tab,WordCloud,Page
from pyecharts.globals import SymbolType
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
#网页爬取模块ss 
def get_html(html,Folder='default',postifix='',cookie=''):
    try:
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
        'Cookie':cookie
       }
        #使用国外代理
        proxies={'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'}
        #get请求获取界面
        html = requests.get(html,headers=headers,proxies=proxies)
        #转码为utf-8
        html.encoding = html.apparent_encoding
        #推导存放路径
        path = './'+Folder+'/'+Folder+postifix+".html"
        #写入文件
        with open(path,"wb") as f:
            f.write(html.content)
            f.close()
    except Exception as e :
        print(e)
    return "ok111"
#时间获取模块
def get_today_data():
    cur_time = datetime.now()
    time = datetime.strftime(cur_time,'%m_%d')#格式化时间字符串
    return time
#本地文件夹文件名提取模块
def get_path(Folder_name):
    path = os.path.abspath('.')
    path_list=os.listdir(str(path)+"\\"+str(Folder_name))
    return path_list
#github网页数据过滤-分模块
def analyze_github(html,time):
    data = []
    #每一页有25个项目，用xpath索引查找
    for i in range(1,25):
        #定义一个字典存放 
        # time时间,title标题
        # text摘要,tages使用的编程语言
        dict={}
        # time就是传入的时间
        dict["time"]=time
        #xpath获取标题
        titles = html.xpath('//*[@id="js-pjax-container"]/div[3]/div/div[2]/article['+str(i)+']/h1/a/text()')
        #去除前后的换行和空格
        title = titles[2].strip('\n').strip(' ').strip('\n')
        dict["title"]=title
        #xpath获取摘要
        text = html.xpath('//*[@id="js-pjax-container"]/div[3]/div/div[2]/article['+str(i)+']/p//text()')
        #摘要可能出现空或者非空，特殊判断下，并去除前后的换行和空格
        if len(text) >=1:
            dict["text"]=text[0].strip('\n').strip(' ').strip('\n')
        else :
            dict["text"]=''
        tag = html.xpath('//*[@id="js-pjax-container"]/div[3]/div/div[2]/article['+str(i)+']/div[2]/span[1]/span[2]//text()')
        #语言标签可能出现空或者非空，特殊判断下，并去除前后的换行和空格
        if len(tag) >=1 :
            dict["tags"]=[]
            dict["tags"].append(tag[0])
        else :
            dict["tags"]=[]
        data.append(dict)
    return data
#stackoverflow网页数据过滤-分模块
def analyze_stackoverflow(html,time):
        data = []
        # re匹配全部热榜问题
        text_all = re.findall('\"([0-9]*)\" data-post-type-id=\"1\">([\s\S]*?)</time>',html,re.S)
        # 将每个问题拆分出来，对问题的id和时间和语言标签进行提取
        for text in text_all:
                #定义一个字典存放 
                # time时间,title标题
                # id 问题id,tage 关键词标签
                dict = {}
                dict["time"]=time
                dict["id"]=eval(text[0])
                dict["tags"]=[]
                # 匹配标题
                titles = re.findall('class=\"s-link\">(.*?)</a>',text[1],re.S)
                dict["title"]=titles[0]
                # 匹配标签
                tags = re.findall('rel=\"tag\">([a-z-+0-9#.]*)',text[1],re.S)
                for tag in tags:
                        dict["tags"].append(tag)
                data.append(dict)
        return data
#分析网页-总模块
def analyze_html(name):
    datas = []
    #读取网站名称，获取他目录下的页面名称列表
    paths_lists = get_path(name)
    for path in paths_lists:
        # 通过字符串处理得到爬取的时间
        time = path.replace(name+"_","").replace(".html","")
        # 传入github分支
        if name.find("github") != -1:
            # 进行etree结构化，使其能被xpath分析
            html = etree.parse(name+'/'+path,etree.HTMLParser())
            data = analyze_github(html,time)
        # 传入Stack Overflow分支
        if name == 'stackoverflow':
            #读取html，re库直接源码匹配即可
            html = open(name+'/'+path,"r",encoding="utf-8").read()
            data = analyze_stackoverflow(html,time)
        for iter in data:
            # 将传出的数据进行汇总到datas中
            datas.append(iter)
    return datas
# categorical_time_data :提取出time和tag
def categorical_time_data(datas):
    # 遍历数据集
    for data in datas:
        # 提取出time和程序语言标签
        time = data["time"]
        tags = data["tags"]
        for tag in tags :
            #如果标签为空，则跳过
            if tag == "":
                continue
            #每循环一次，返回一个元组(time,tag)
            #python语法糖
            yield (time,tag)
# merge_all_time_data : 将Stack Overflow和github的网站数据合并
def merge_all_time_data(all_datas):
    tag_datas={}
    #tot用于统计全部的，不论任何时间的
    tag_datas["tot"] = []
    #遍历数据结构，进行time和tag的提取
    for datas in all_datas:
        # 通过提取time和tag模块，得到time和tag数据
        for time,tag in  categorical_time_data(datas):
            # 对tot推入所有tag
            tag_datas["tot"].append(tag)
            # 将tag按时间分类
            if time not in tag_datas:
                tag_datas[time]=[]
                tag_datas[time].append(tag)
            else :
                tag_datas[time].append(tag)
    return tag_datas
def categorical_title_data(datas):
    for data in datas:
        # 提取出标题数据
        title = data["title"]
        # 将数据用jieba分词，存入列表
        list = jieba.cut(title)
        #遍历每一个分词出的单词
        for word in list:
            # 传回得到的单词
            yield word
def merge_all_title_data(all_datas):
    words = {}
    for datas in all_datas:
        #得到词频
        for word in categorical_title_data(datas):
            # 通过re库过滤 一些短的词，防止人称等无用词干扰
            # （虽然有失偏驳，但是就先这样吧）
            if re.search("^.{5,50}",word) == None:
                continue
            # 将单词通过字典存储
            if word not in words:
                words[word]=1
            else :
                words[word]+=1
    words = sorted(words.items(),key = lambda x:x[1],reverse=True)
    return words
# get_top_7 : 得到top7，以及其在每日中变化趋势
def get_top_7(data):
    # 从time_tag数据中转模块得到数据结构
    time_datas = merge_all_time_data(data)

    # 通过python自带的频率分析函数 得到每个语言的出现次数，在tot中得到前7
    dict_tmp = collections.Counter(time_datas['tot'])
    # 将得到的频率排序
    tot_rank=sorted(dict_tmp.items(),key=lambda x:x[1],reverse=True)
    top_list = [] #存放排名前7的语言元组
    time_lab=[] #存放日期标签
    top_lab=[] #存放排名前7的语言标签
    top_list_everyday = {}#存放各个日期出现的次数

    #遍历前7个出现最多的语言个数，放入上面准备好的列表中
    for index in range(7):
        top_list.append(tot_rank[index])
        top_lab.append(tot_rank[index][0])
    
    #按前7个出现最多的语言去统计得到 各个日期的数据结构
    for time,data in time_datas.items():
        if time != "tot":
            time_lab.append(time)
            # 对各个天数的日期进行频率统计
            dict_tmp = collections.Counter(time_datas[time])
            top_list_everyday[time] = []
            for name,value in dict_tmp.items():
                # 如果语言是前7的语言标签，则放入数据结构
                if name in top_lab:
                    top_list_everyday[time].append((name,value))
            # 将得到东西排个序
            top_list_everyday[time] = sorted(top_list_everyday[time],key=lambda x:x[1],reverse=True)
    #把tot也放进去
    top_list_everyday["tot"]=top_list
    #无所谓的特殊处理
    top_lab.reverse()
    #将时间标签，前7个热门语言标签，和对应的key,value返回
    return time_lab,top_lab,top_list_everyday
def make_bar_3d_data(time_lab,top_lab,top_list):
    bar_3d_data = []
    for time,list in top_list.items():
        if time in time_lab:
            i = time_lab.index(time)
            for name,value in list:
                j = top_lab.index(name)
                z = value
                bar_3d_data.append([i,j,z])
    return bar_3d_data
def make_line_data(time_lab,top_lab,top_list):
    line_data = {}
    for lab in top_lab:
        line_data[lab]=[]
        for time in time_lab:
            flag = True
            for data in top_list[time]:
                # print(data)
                if data[0] == lab:
                    flag = False
                    line_data[lab].append(data[1])
            if flag :
                line_data[lab].append(0)
    return line_data
def draw_bar_3d(all_time_lab,all_top_lab,all_top_list,title):
    datas = make_bar_3d_data(all_time_lab,all_top_lab,all_top_list)
    bar = (
    Bar3D(init_opts=opts.InitOpts(width="1400px", height="600px"))
    .add(
        series_name="",
        data=datas,
        xaxis3d_opts=opts.Axis3DOpts(type_="category", data=all_time_lab),
        yaxis3d_opts=opts.Axis3DOpts(type_="category", data=all_top_lab),
        zaxis3d_opts=opts.Axis3DOpts(type_="value"),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title=title),
        visualmap_opts=opts.VisualMapOpts(
            max_=20,
            range_color=[
                "#313695",
                "#4575b4",
                "#74add1",
                "#abd9e9",
                "#e0f3f8",
                "#ffffbf",
                "#fee090",
                "#fdae61",
                "#f46d43",
                "#d73027",
                "#a50026",
            ],
        )
    )
    )
    return bar
def draw_line(time_lab,top_lab,top_list,title):
    datas = make_line_data(time_lab,top_lab,top_list)
    line = (
    Line(init_opts=opts.InitOpts(width="1600px", height="800px"))
    .add_xaxis(time_lab)
    .add_yaxis(top_lab[0], datas[top_lab[0]])
    .add_yaxis(top_lab[1], datas[top_lab[1]])
    .add_yaxis(top_lab[2], datas[top_lab[2]])
    .add_yaxis(top_lab[3], datas[top_lab[3]])
    .add_yaxis(top_lab[4], datas[top_lab[4]])
    .add_yaxis(top_lab[5], datas[top_lab[5]])
    .add_yaxis(top_lab[6], datas[top_lab[6]])
    .set_global_opts(
        title_opts=opts.TitleOpts(title=title),
        visualmap_opts=opts.VisualMapOpts(type_="size", max_=30, min_=0),
        )

    )
    return line
def draw_pie(top_list,title):
    pie = (
    Pie(init_opts=opts.InitOpts(width="800px", height="800px", bg_color="#ffffff"))
    .add(
        series_name="数据",
        data_pair=top_list,
        rosetype="radius",
        radius="55%",
        center=["50%", "50%"],
        label_opts=opts.LabelOpts(is_show=False, position="center"),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title=title,
            pos_left="center",
            pos_top="20",
            title_textstyle_opts=opts.TextStyleOpts(color="#000000"),
        ),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    .set_series_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
        ),
        label_opts=opts.LabelOpts(color="rgba(0, 0, 0, 0.3)"),
    )
    )
    return pie
def draw_pie_tab(datas,title):
    pie_datas={}
    for name,value in datas.items():
        pie = draw_pie(value,title+" "+name+" 饼状图")
        pie_datas[name]=pie
    tab = Tab()
    for name,chart in pie_datas.items():
        tab.add(chart,name)
    return tab
def draw_wordcloud(words,title):
    cloud = (
    WordCloud(init_opts=opts.InitOpts(width="1000px", height="500px"))
    .add("", words, word_size_range=[20, 100], shape=SymbolType.DIAMOND)
    .set_global_opts(title_opts=opts.TitleOpts(title=title))
    )
    return cloud
if __name__ == "__main__":
    graphviz = GraphvizOutput()
    graphviz.output_file = '数据归类.png'
    stackoverflow_datas = analyze_html('stackoverflow')
    github_today_datas = analyze_html('github_today')
    with PyCallGraph(output=graphviz):
        # today = get_today_data()
        # get_html('https://stackoverflow.com/?tab=hot','stackoverflow','_'+today)
        # get_html('https://github.com/trending?since=daily','github_today','_'+today)
        all_time_lab,all_top_lab,all_top_list = get_top_7([github_today_datas,stackoverflow_datas])
        github_time_lab,github_top_lab,github_top_list = get_top_7([github_today_datas])
        stackoverflow_time_lab,stackoverflow_top_lab,stackoverflow_top_list = get_top_7([stackoverflow_datas])
        all_title_data = merge_all_title_data([github_today_datas,stackoverflow_datas])
    cloud = draw_wordcloud(all_title_data,"聚合标题词云图")
    github_tab = draw_pie_tab(github_top_list,"github ")
    stackoverflow_tab = draw_pie_tab(stackoverflow_top_list," stackoverflow ")
    bar_3d = draw_bar_3d(all_time_lab,all_top_lab,all_top_list,title="聚合趋势3D柱状图")
    github_line = draw_line(github_time_lab,github_top_lab,github_top_list,title="github排行榜语言趋势折线图")
    stackoverflow_line = draw_line(stackoverflow_time_lab,stackoverflow_top_lab,stackoverflow_top_list,title="StackOverflow排行榜语言趋势折线图")
    cloud.render("cloud.html")
    github_tab.render("github_tab.html")
    stackoverflow_tab.render("stackoverflow_tab.html")
    github_line.render("github_line.html")
    stackoverflow_line.render("stackoverflow_line.html")
    bar_3d.render("bar_3d.html")