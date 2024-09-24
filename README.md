# 介绍

AI 一键出书 -by 云中江树

书生浦语大模型训练营，提示工程实践开源项目。

在线体验链接：
https://book.apps.langgpt.ai/

## 配置环境
```
pip install openai, phidata, python-dotenv
pip install -r requirements.txt
```

## 运行项目

前往[硅基流动](https://cloud.siliconflow.cn/i/TxUlXG3u)注册免费的 API，获取 API_KEY
> https://cloud.siliconflow.cn/i/TxUlXG3u
```
export API_KEY=sk-xxx
export BASE_URL=https://api.siliconflow.cn/v1
export MODEL_NAME=internlm/internlm2_5-7b-chat

python3 book_writer.py
```

## 致谢
- 书生浦语大模型