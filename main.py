import machine
import time
from mpu6050 import MPU6050, RANGE_4G


def main():
    i2c = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3))
    mpu6050 = MPU6050(i2c, range=RANGE_4G)

    if mpu6050.is_device_accessible():
        mpu6050.start()

        print(f"Accelerometer range: {mpu6050.accelerometer_range}")

        for _ in range(50):
            acc = [round(i, 1) for i in mpu6050.get_acceleration()]
            print(f"X:{acc[0]} | Y:{acc[1]} | Z:{acc[2]}")

            time.sleep(0.5)

        mpu6050.stop()


if __name__ == '__main__':
    main()