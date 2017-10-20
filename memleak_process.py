#! -*- coding:utf-8 -*-

# 处理 memory.log 文件
# 要求：
#          1. 先 ======>>start  再 ======>>end
#          2. 先 jet_malloc 再 jet_free
#          3.  jet_malloc 与 jet_free 前一行开头必须为 jet_assert
#          4. 以下例子中 ...... 可以为任意内容
#          5.  jet_malloc 与 jet_free 英文冒号后跟的数据必须相同
#          6. 删除符合条件的 jet_assert jet_malloc jet_assert 这四行
#
# eg: 例子中，中间四行符合规则需要删除。
#
# ======>>start ......
# jet_assert ......
# jet_malloc:0x12345678
# jet_assert ......
# jet_free:0x12345678
# ======>>end ......
#
# 处理好后将剩余项保存到 cut_memory.log 文件中

# changelog:
# 2017.10.19 : 学习正则解析式子
# 2017.10.20 ：完成功能
#


import os
import re

KeyValue = [
    r'======>>start(.*)',
    r'jet_malloc:0x[a-fA-F0-9]{8}',
    r'jet_assert (.*)', # 前向查找 jet_assert ...... \r\n 到\n 结束 提前删除\r\n有利于完整匹配
    r'jet_free:0x[a-fA-F0-9]{8}',  #[0-9]*8 匹配地址8位的
    r'0x[a-fA-F0-9]{8}',
    r'======>>end(.*)',
    r'jet_free:',
]

# 判断文件在否并读入到内存缓冲区,
def JetLogRead(filename):
    # 判断文件是否存在
    if False == os.path.exists(filename):
        print('%s not exist\n' % filename)
        return

    # 判断文件是否可读
    if False == os.access(filename,os.R_OK) :
        print('%s is unaccessible to read \n' % filename)
        return

    # read file
    ret_val = open(filename,'rb').read()

    return ret_val


#保存文件
def JetLogSave(FileName,Value):
    NewValue = Value.encode('ascii')
    try:
        f = open(FileName,'wb')
        f.write(NewValue)
    except ValueError:
        print('New File save error')


# 处理内容
def ValueProcess(Value):
    encoding = 'ascii'

    NewValue = Value.decode(encoding)  # 先解码

    FinalBuf = '======>>start \n\r'

    # 先找寻 ======>>start 确定区间
    Start = re.search(KeyValue[0],NewValue)
    if Start == None:
        return    # 初始条件没找到
    End   = re.search(KeyValue[5],NewValue)
    if End   == None:
        return    # 结束条件没找到

    # 在一次搜寻的 ========>>start ========>>end 中进行查找

    # 事先进行一次搜索，确定有 jet_malloc：

    StartEndBuf = NewValue[Start.end():End.start()].lstrip('\r\n')

    MallocStart = re.search(KeyValue[1],StartEndBuf)

    if MallocStart == None:
        print('start none \n')

    # 循环初始条件

    buf    = NewValue[Start.end():End.start()]
    count  = 0

    while True:  # 循环处理
        Newbuf , err = FindAndDeleteKeyValue(buf)

        print('NewBuf:',len(Newbuf),'err:',err)

        if err != 5:
            if err == 1:   # 没有找到jet_malloc
                # 直接退出循环
                print("summary: may have %d position memory leak\n"%count)
                break;
            elif err == 2: # 找到了jet_malloc 但是没有找到对应的 jet_free
                # 需要找到jet_malloc的位置并缩小范围
                TempMalloc = re.search(KeyValue[1], buf[0:len(buf)])
                FinalBuf += buf[0:TempMalloc.end()]
                buf = Newbuf[TempMalloc.end():]
                count += 1
            elif err == 3: # 删除 jet_malloc 前一行时候出现了错误
                # 直接出问题
                print('error 3')
                os.abort()
            elif err == 4: # 删除 jet_free 前一行出现了错误
                # 直接出问题
                print('error 4')
                print(Newbuf)
                os.abort()
        else:
            buf = Newbuf

    FinalBuf += '\r\n======>>end \r\n'
    print('FinalBuf:\n',FinalBuf)
    return FinalBuf


# 查找一段 string 数据中的 指定 jet_malloc 和 jet_free
# 成功返回处理后的数据，不成功返回None

def FindAndDeleteKeyValue(Value):
    NewValue = Value

    # 找到 jet_malloc:0xaaaaaaaa 位置
    JetMalloc  = re.search(KeyValue[1], NewValue)
    if JetMalloc == None:
        return Value,1 # 没有找到 jet_malloc

    MallocAddr = re.search(KeyValue[4], JetMalloc.group())

    # 找寻是否含有 jet_free:0xaaaaaaaa 位置
    FreeValue = NewValue[JetMalloc.end():]

    JetFree = re.search(KeyValue[6] + MallocAddr.group(), FreeValue)
    if JetFree == None:
        return Value,2  # 找到jet_malloc 但是没找到对应的 jet_free

    # 删除 jet_malloc:0xaaaaaaa 前一行
    MallocUpBuf = NewValue[:JetMalloc.start()].rstrip('\r\n') + NewValue[JetMalloc.start():JetMalloc.end()]
    MallocUp = re.search(KeyValue[2] + NewValue[JetMalloc.start():JetMalloc.end()], MallocUpBuf)
    if MallocUp == None:
        return Value,3  # 没找到 jet_malloc以及匹配的前面一行 暂时退出

    # 删除 jet_free:0xaaaaaaaa 以及前一行
    FreeUPBuf  = FreeValue[:JetFree.start()].rstrip('\r\n')
    FreeUPBuf += FreeValue[JetFree.start():JetFree.end()]
    FreeUp = re.search(KeyValue[2] + FreeValue[JetFree.start():JetFree.end()], FreeUPBuf)
    if FreeUp == None:
        return Value,4  # 没找到 jet_free 以及匹配的前面一行 暂时退出

    # 拼接新数组
    BufCutMallocFree = NewValue[:MallocUp.start()].rstrip('\r\n')+ \
                       FreeValue[:FreeUp.start()].rstrip('\r\n')+ \
                       FreeValue[FreeUp.end()+2:].rstrip('\r\n')

    return BufCutMallocFree,5



ret_val = JetLogRead('memory.log') #默认当前目录下
if ret_val == None :
    exit(-1)

NewValue = ValueProcess(ret_val)
JetLogSave('CutMemory.log',NewValue)










