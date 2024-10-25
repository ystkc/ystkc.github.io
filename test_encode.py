def encoder(text):
    # 转化成bytearray类型
    input = bytearray(text.encode())
    
    for i in range(len(input)):
        # 将byte的后5位取反
        input[i] = input[i] ^ 0b00011111
    
    return input

def decoder(input):
    # 转化成bytearray类型
    
    for i in range(len(input)):
        # 将byte的后5位取反
        input[i] = input[i] ^ 0b00011111
    
    return input.decode()


input_text = input("请输入要加密的文本：")

encrypted_text = encoder(input_text)
print("加密后的文本：", encrypted_text)

decrypted_text = decoder(encrypted_text)
print("解密后的文本：", decrypted_text)