from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from flask import jsonify
import openai
import os

# 建议你在环境变量设置密钥，默认写法为读取 OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        city = data.get('city')
        purchase_price = data.get('purchase_price')
        area = data.get('area')
        current_price = data.get('current_price')
        rent = data.get('rent')

        # 构造 prompt
        prompt = f"""
        城市：{city}
        购房价格：{purchase_price}元
        面积：{area}㎡
        当前市场单价：{current_price}元/㎡
        当前租金：{rent}元/月

        请以现实派逻辑，结合中国市场趋势，预测该房产未来五年每年房价走势和租金收益率。
        返回格式为 JSON，字段包括：
        {{
          "predicted_price_per_year": {{
            "2025": xxxx,
            "2026": xxxx,
            ...
          }},
          "roi_per_year": {{
            "2025": "xx%",
            ...
          }}
        }}
        """

        # 调用 ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()

        # 转换为字典返回（OpenAI 返回的是文本）
        result = eval(content)  # 或使用 json.loads() 更安全
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)
