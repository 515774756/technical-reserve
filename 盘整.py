# 导入pandas和numpy库
import pandas as pd
import numpy as np


# 定义一个函数，用来计算MACD的值
def macd(df, fastperiod=12, slowperiod=26, signalperiod=9):
    # 计算快速和慢速的指数移动平均线
    ema_fast = df["close"].ewm(span=fastperiod, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slowperiod, adjust=False).mean()
    # 计算差离值
    diff = ema_fast - ema_slow
    # 计算信号线
    dea = diff.ewm(span=signalperiod, adjust=False).mean()
    # 计算柱状图
    bar = 2 * (diff - dea)
    # 返回结果
    return diff, dea, bar


# 定义一个函数，用来划分线段
def segment(df):
    # 初始化一个空列表，用来存储线段的端点
    points = []
    # 初始化一个变量，用来记录当前的走势方向，1为向上，-1为向下，0为不确定
    direction = 0
    # 遍历数据框的每一行
    for i in range(len(df)):
        # 获取当前行的收盘价
        price = df.iloc[i]["close"]
        # 如果还没有找到第一个端点，就继续寻找
        if len(points) == 0:
            # 如果当前方向是不确定的，就以当前价格作为临时端点
            if direction == 0:
                points.append(price)
                continue
            # 如果当前方向是向上的，就判断当前价格是否高于临时端点
            elif direction == 1:
                if price > points[-1]:
                    # 如果是，就更新临时端点为当前价格
                    points[-1] = price
                    continue
                else:
                    # 如果不是，就说明出现了向下的拐点，就把临时端点确定为第一个端点，并把当前价格作为第二个临时端点，同时改变方向为向下
                    points.append(price)
                    direction = -1
                    continue
            # 如果当前方向是向下的，就判断当前价格是否低于临时端点
            elif direction == -1:
                if price < points[-1]:
                    # 如果是，就更新临时端点为当前价格
                    points[-1] = price
                    continue
                else:
                    # 如果不是，就说明出现了向上的拐点，就把临时端点确定为第一个端点，并把当前价格作为第二个临时端点，同时改变方向为向上
                    points.append(price)
                    direction = 1
                    continue

        # 如果已经找到了第一个端点，就开始划分线段
        else:
            # 如果当前方向是向上的，就判断当前价格是否高于最后一个端点
            if direction == 1:
                if price > points[-1]:
                    # 如果是，就更新最后一个端点为当前价格，并继续寻找拐点
                    points[-1] = price
                    continue
                else:
                    # 如果不是，就判断当前价格是否低于倒数第三个端点（如果存在的话）
                    if len(points) >= 3 and price < points[-3]:
                        # 如果是，就说明出现了中枢破坏，就删除倒数第二个端点，并把当前价格作为新的端点，同时改变方向为向下，并继续寻找拐点
                        points.pop(-2)
                        points.append(price)
                        direction = -1
                        continue
                    else:
                        # 如果不是，就判断当前价格是否低于倒数第二个端点减去一定的比例（这里取收盘价的3%）
                        if price < points[-2] - 0.03 * df.iloc[i]["close"]:
                            # 如果是，就说明出现了有效的向下拐点，就把当前价格作为新的端点，并改变方向为向下，并继续寻找拐点
                            points.append(price)
                            direction = -1
                            continue

            # 如果当前方向是向下的，就判断当前价格是否低于最后一个端点            
            elif direction == -1:
                if price < points[-1]:
                    # 如果是，就更新最后一个端点为当前价格，并继续寻找拐点
                    points[-1] = price
                    continue
                else:
                    # 如果不是，就判断当前价格是否高于倒数第三个端点（如果存在的话）
                    if len(points) >= 3 and price > points[-3]:
                        # 如果是，就说明出现了中枢破坏，就删除倒数第二个端点，并把当前价格作为新的端点，并改变方向为向上，并继续寻找拐点 
                        points.pop(-2)
                        points.append(price)
                        direction = 1
                        continue
                    else:
                        # 如果不是，就判断当前价格是否高于倒数第二个端点加上一定的比例（这里取收盘价的3%）
                        if price > points[-2] + 0.03 * df.iloc[i]["close"]:
                            # 如果是，就说明出现了有效的向上拐点，就把当前价格作为新的端点，并改变方向为向上，并继续寻找拐点 
                            points.append(price)
                            direction = 1
                            continue

                            # 返回线段的端点列表
    return points


# 定义一个函数，用来判断中枢和背驰
def zhongshu_and_beichi(df):
    # 调用macd函数，计算MACD的值，并添加到数据框中    
    df["diff"], df["dea"], df["bar"] = macd(df)
    # 调用segment函数，划分线段，并获取线段的端点列表    
    points = segment(df)
    # 初始化一个空列表，用来存储中枢的起始和结束位置    
    zhongshu_pos = []
    # 初始化一个变量，用来记录当前是否在中枢中，True为是，False为否    
    in_zhongshu = False
    # 初始化四个变量，用来记录中枢的高低区间    
    zhongshu_high = None
    zhongshu_low = None
    zhongshu_high2 = None
    zhongshu_low2 = None
    # 遍历线段的每个端点    
    for i in range(len(points)):
        # 获取当前端点对应的收盘价        
        price = points[i]
        # 如果还没有形成中枢        
        if not in_zhongshu:
            # 判断是否有足够的端点来形成中枢            
            if i + 4 < len(points):
                # 获取相邻的五个端点                
                p1, p2, p3, p4, p5 = points[i:i + 5]
                # 判断是否满足中枢形成的条件                
                if min(p1, p3) > max(p2, p4) or max(p1, p3) < min(p2, p4):
                    # 如果满足，就记录中枢的高低区间                    
                    zhongshu_high = min(p1, p3)
                    zhongshu_low = max(p2, p4)
                    zhongshu_high2 = min(p3, p5)
                    zhongshu_low2 = max(p4, p5)
                    # 把中枢形成位置添加到列表中                    
                    zhongshu_pos.append(i + 2)
                    zhongshu_pos.append(i + 4)
                    # 改变状态为在中枢中                    
                    in_zhongshu = True
        else:
            # 如果已经形成中枢
            # 判断当前端点是否在中枢区间内
            if zhongshu_low <= price <= zhongshu_high:
                # 如果是，就更新中枢的高低区间
                zhongshu_high = max(zhongshu_high, zhongshu_high2)
                zhongshu_low = min(zhongshu_low, zhongshu_low2)
                # 把当前端点位置添加到列表中
                zhongshu_pos.append(i)
            else:
                # 如果不是，就判断是否有足够的端点来更新中枢
                if i + 2 < len(points):
                    # 获取相邻的三个端点
                    p1, p2, p3 = points[i:i + 3]
                    # 判断是否满足中枢更新的条件
                    if min(p1, p3) > zhongshu_low and max(p1, p3) < zhongshu_high:
                        # 如果满足，就更新中枢的高低区间
                        zhongshu_high2 = min(p1, p3)
                        zhongshu_low2 = max(p2, p3)
                        # 把当前端点位置添加到列表中
                        zhongshu_pos.append(i)
                        zhongshu_pos.append(i + 2)
                    else:
                        # 如果不满足，就说明中枢结束，记录中枢结束的位置
                        zhongshu_pos.append(i - 1)
                        # 改变状态为不在中枢中
                        in_zhongshu = False
                else:
                    # 如果没有足够的端点来更新中枢，就说明中枢结束，记录中枢结束的位置
                    zhongshu_pos.append(i - 1)
                    # 改变状态为不在中枢中
                    in_zhongshu = False

                    # 初始化一个空列表，用来存储背驰的位置和类型
        beichi_pos = []
        beichi_type = []
        # 遍历所有的中枢位置
        for i in range(0, len(zhongshu_pos), 2):
            # 获取当前中枢的起始和结束位置
            start = zhongshu_pos[i]
            end = zhongshu_pos[i + 1]
            # 获取当前中枢前后的线段端点
            prev_point = points[start - 1]
            next_point = points[end + 1]
            curr_point = points[end]
            # 判断当前中枢是向上还是向下
            if curr_point > prev_point:
                # 如果是向上，就计算前后两段的MACD柱状图面积之和
                prev_area = df.iloc[start - 1:end + 1]["bar"].sum()
                next_area = df.iloc[end:end + 3]["bar"].sum()
                # 如果后面的面积小于前面的面积，就判断为上涨背驰，并记录位置和类型
                if next_area < prev_area:
                    beichi_pos.append(end + 1)
                    beichi_type.append("上涨背驰")
            else:
                # 如果是向下，就计算前后两段的MACD柱状图面积之和
                prev_area = df.iloc[start - 1:end + 1]["bar"].sum()
                next_area = df.iloc[end:end + 3]["bar"].sum()
                # 如果后面的面积大于前面的面积，就判断为下跌背驰，并记录位置和类型
                if next_area > prev_area:
                    beichi_pos.append(end + 1)
                    beichi_type.append("下跌背驰")

        # 返回背驰的位置和类型列表
        return beichi_pos, beichi_type

        # 读取数据文件，假设是日线数据，有日期、开盘价、最高价、最低价、收盘价、成交量等列
    df = pd.read_csv("data.csv")
    # 调用zhongshu_and_beichi函数，判断中枢和背驰，并获取背驰的位置和类型列表
    beichi_pos, beichi_type = zhongshu_and_beichi(df)
    # 打印结果
    print("识别到以下背驰：")
    for i in range(len(beichi_pos)):
        print(f"{df.iloc[beichi_pos[i]]['date']}出现{beichi_type[i]}")
