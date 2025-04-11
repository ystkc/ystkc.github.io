# 目前tensorflowjs==4.22.0因为包含了tensorflow_decision_forests，仅支持linux、MacOS

# 创建环境（windows）：
# 清理C盘确认有5G
# 安装基于win11的Hyper-V
# taskmgr确认虚拟化已开启
# 重启并通过appwiz.cpl确认启用了虚拟...程序
# 确认bcdedit /enum | findstr -i hypervisorlaunchtype 不是 false （bcdedit /set hypervisorlaunchtype auto + 重启）

# 安装wsl2:
# wsl --set-default-version 2
# wsl --install -d Ubuntu-22.04

# 启动环境：
# sudo apt update && sudo apt upgrade -y
# sudo apt install build-essential python3-pip libreadline-dev
# python3 -m venv tdf_env  # 创建虚拟环境在当前shell目录下/tdf_env

# 安装python库、ITEX
# tdf_env/bin/pip install tensorflowjs==4.22.0 tf.keras==3.9.2 scikit-learn==1.6.1 intel-extension-for-tensorflow==0.0.0.dev1 wget
# sudo apt install -y libstdc++6 ocl-icd-libopencl1
# wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/e6ff8e9c-ee28-47fb-abd7-5c524c983e1c/l_BaseKit_p_2024.2.1.100_offline.sh # 下载ITEX安装包
# sudo sh l_BaseKit_p_2024.2.1.100_offline.sh # 安装ITEX
# \l_BaseKit_p_2024.2.1.100_offline\install.sh # (功能同上，解压后的脚本)运行ITEX安装脚本
# source /opt/intel/oneapi/setvars.sh # 加载环境变量

# build ITEX
# sudo apt install unzip # 如果没有unzip，请安装
# wget https://github.com/bazelbuild/bazel/releases/download/5.3.0/bazel-5.3.0-installer-linux-x86_64.sh # 需要bazel进行build
# bash bazel-5.3.0-installer-linux-x86_64.sh --user
# git clone https://github.com/intel/intel-extension-for-tensorflow.git intel-extension-for-tensorflow # 下载代码
# ./configure # 按照https://intel.github.io/intel-extension-for-tensorflow/latest/docs/install/how_to_build.html#build-intel-extension-for-tensorflow-pypi来配置
# sudo apt-get install level-zero-dev

# cd intel-extension-for-tensorflow
# bazel build -c opt --config=xpu  //itex/tools/pip_package:build_pip_package

# 运行
# tdf_env/bin/python train.py
# 

# -------
# 使用intel-extension-for-tensorflow
# from intel_extension_for_tensorflow.python.ops import Init
# Init()
import tensorflow as tf
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflowjs as tfjs
import numpy as np
import json


# 配置参数
CONFIG = {
    "data_path": "./category/软色情.csv",         # 数据集路径（需包含text和label列）
    "text_column": "text",           # 文本列名
    "label_column": "label",         # 标签列名
    "max_words": 5000,              # 最大词汇量
    "max_seq_length": 100,           # 序列最大长度
    "embedding_dim": 64,             # 嵌入维度
    "model_save_path": "./model/test.keras",    # 模型保存路径
    "tfjs_target_dir": "./model",  # TF.js模型输出目录
    "test_size": 0.2,               # 验证集比例
    "batch_size": 32,
    "epochs": 20
}

# 数据预处理管道
def preprocess_data():
    # 加载数据
    df = pd.read_csv(CONFIG["data_path"])
    texts = df[CONFIG["text_column"]].values.astype(str)
    labels = df[CONFIG["label_column"]].values

    # 清洗文本（按需扩展）
    texts = [t.lower().replace(r'[^\w\s]', '') for t in texts]

    # 划分数据集
    X_train, X_val, y_train, y_val = train_test_split(
        texts, labels, test_size=CONFIG["test_size"], random_state=42
    )

    # 文本向量化
    tokenizer = Tokenizer(num_words=CONFIG["max_words"], oov_token="<OOV>")
    tokenizer.fit_on_texts(X_train)
    
    # 转换为序列
    train_sequences = tokenizer.texts_to_sequences(X_train)
    val_sequences = tokenizer.texts_to_sequences(X_val)
    
    # 填充序列
    X_train = pad_sequences(train_sequences, maxlen=CONFIG["max_seq_length"])
    X_val = pad_sequences(val_sequences, maxlen=CONFIG["max_seq_length"])

    # 标签编码
    num_classes = len(set(labels))
    y_train = tf.keras.utils.to_categorical(y_train, num_classes)
    y_val = tf.keras.utils.to_categorical(y_val, num_classes)

    return X_train, X_val, y_train, y_val, tokenizer, num_classes

# 构建轻量级模型
def build_model(input_shape, num_classes):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=input_shape),
        tf.keras.layers.Embedding(
            input_dim=CONFIG["max_words"], 
            output_dim=CONFIG["embedding_dim"]
        ),
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(24, activation="relu"),
        tf.keras.layers.Dense(num_classes, activation="softmax")
    ])
    
    model.compile(
        loss="categorical_crossentropy",
        optimizer="adam",
        metrics=["accuracy"]
    )
    return model

# 训练流程
def train():
    # 数据预处理
    X_train, X_val, y_train, y_val, tokenizer, num_classes = preprocess_data()
    
    # 构建模型
    model = build_model((CONFIG["max_seq_length"],), num_classes)
    
    # 训练配置
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=3, restore_best_weights=True
    )
    
    # 开始训练
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=CONFIG["epochs"],
        batch_size=CONFIG["batch_size"],
        callbacks=[early_stop]
    )
    
    # 保存完整模型
    model.save(CONFIG["model_save_path"])
    
    # 导出为TF.js格式
    # tfjs.converters.save_tf.keras_model(
    #     model, 
    #     CONFIG["tfjs_target_dir"],
    #     quantization_dtype_map={tf.float16: np.float16}  # 可选量化
    # )
    # $ tensorflowjs_converter --input_format=keras /model/test.h5 /model/tfjs_test
    
    # 保存词汇表（前端预处理需要）
    with open(f"{CONFIG['tfjs_target_dir']}/vocab.json", "w") as f:
        json.dump(tokenizer.word_index, f)
    
    print(f"模型已导出至 {CONFIG['tfjs_target_dir']}")

def predict():
    # 加载模型
    model = tf.keras.models.load_model(CONFIG["model_save_path"])
    
    # 加载词汇表
    with open(f"{CONFIG['tfjs_target_dir']}/vocab.json", "r") as f:
        word_index = json.load(f)
    
    # 预测
    tokenizer = Tokenizer(num_words=CONFIG["max_words"], oov_token="<OOV>")
    while True:
        text = input("请输入文本(#退出)：")
        s = ''
        while s != "#":
            s = input("请输入文本(#退出)：")
            text += s
        sequence = tokenizer.texts_to_sequences([text])
        padded_sequence = pad_sequences(sequence, maxlen=CONFIG["max_seq_length"])
        prediction = model.predict(padded_sequence)
        print(prediction)

if __name__ == "__main__":
    if input('1=train 2=predict: ') == '1':
        train()
    else:
        predict()
