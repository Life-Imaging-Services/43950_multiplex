import time
import conf
import slf3s_jad


slf3 = slf3s_jad.SLF3S_1300(conf.i2c_flow_sensor,'h2o')
time.sleep(0.1)
print(slf3.read_sensor())
print(slf3.read_flow())
print(slf3.read_temp())
