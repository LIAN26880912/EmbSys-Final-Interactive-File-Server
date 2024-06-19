import libmpu9250
import numpy as np
import math, time

def IMU_sense(flags):
    # Not tested
    mpu9250 = libmpu9250.MPU9250()
    accel_bias = mpu9250.readAccel()    # Assume horizontal in the beginning
    accel_bias['z'] -= 1        # Due to gravity
    accel_threshold = np.sqrt(2)    # The valuse is TBD (in g)

    while True:
        end_flag = flags['end']
        if end_flag:
            print("End IMU sensing")
            break
        accel_cur = mpu9250.readAccel()
        accel_cur = {k:accel_cur[k] - accel_bias[k] for k in accel_cur.keys()}
        accel_norm = np.linalg.norm(accel_cur)
        flags['falling'] = accel_norm >= accel_threshold
        time.sleep(0.1)
        
            
        
