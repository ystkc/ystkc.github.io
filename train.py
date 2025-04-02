import tensorflow as tf
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflowjs as tfjs
import numpy as np
import re



# 配置参数
CONFIG = {
    "data_path": "data.csv",         # 数据集路径（需包含text和label列）
    "text_column": "text",           # 文本列名
    "label_column": "label",         # 标签列名
    "max_words": 5000,              # 最大词汇量
    "max_seq_length": 100,           # 序列最大长度
    "embedding_dim": 64,             # 嵌入维度
    "model_save_path": "./model",    # 模型保存路径
    "tfjs_target_dir": "./tfjs_model",  # TF.js模型输出目录
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
    tfjs.converters.save_keras_model(
        model, 
        CONFIG["tfjs_target_dir"],
        quantization_dtype_map={tf.float16: np.float16}  # 可选量化
    )
    
    # 保存词汇表（前端预处理需要）
    with open(f"{CONFIG['tfjs_target_dir']}/vocab.json", "w") as f:
        json.dump(tokenizer.word_index, f)
    
    print(f"模型已导出至 {CONFIG['tfjs_target_dir']}")

if __name__ == "__main__":
    train()