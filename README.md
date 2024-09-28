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

1. 前往[硅基流动](https://cloud.siliconflow.cn/i/TxUlXG3u)注册免费的 API，获取 API_KEY
> https://cloud.siliconflow.cn/i/TxUlXG3u

2. 下载代码到本地
```
git clone https://github.com/langgptai/BookAI.git
cd BookAI
```

3. 运行下面的指令
```
export API_KEY=sk-xxx
export BASE_URL=https://api.siliconflow.cn/v1
export MODEL_NAME=internlm/internlm2_5-7b-chat

python3 book_writer.py
```

4. 生成的书籍保存在 books 文件夹下，使用 markdown 编辑器打开查看。

## 致谢
- 书生浦语大模型