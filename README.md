## CLeak_tool
[中文帮助](http://www.jianshu.com/p/b0b4e59dc947)


A memory.log process tool

memory.log format:
```c
======>>start
jet_assert malloc:ACInterface.c, func: CWInterface,line 717
jet_malloc:0x015af878
jet_assert free  :CWThread.c, func: CWHandleTimer,line 720
jet_free:0x015b1f60
jet_assert free  :CWThread.c, func: CWHandleTimer,line 721
jet_free:0x015ae480
jet_assert malloc:CWThread.c, func: CWTimerRequest,line 733
jet_malloc:0x015b1c08
jet_assert malloc:CWThread.c, func: CWTimerRequest,line 734
jet_malloc:0x015d32e8
======>>end
```

python tool will delete the line that "jet_malloc:address == jet_free:address" and copy to new file CutMemory.log such as:


>memory.log
```c
======>>start
jet_assert malloc:ACInterface.c, func: CWInterface,line 717
jet_malloc:0x015af878
jet_assert free  :CWThread.c, func: CWHandleTimer,line 720
jet_free:0x015af878
jet_assert malloc:CWThread.c, func: CWTimerRequest,line 734
jet_malloc:0x015d32e8
======>>end
```

>Cutmemory.log
```c
======>>start
jet_assert malloc:CWThread.c, func: CWTimerRequest,line 734
jet_malloc:0x015d32e8
======>>end
```

Easy to carry out memory analysis


