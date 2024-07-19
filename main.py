import machine
import time
from mpu6050 import MPU6050, RANGE_4G, RANGE_250


def round_readings(data: list[float], round_val: int = 2) -> list[float]:
    return [round(i, round_val) for i in data]


def main():
    i2c = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3))
    mpu6050 = MPU6050(i2c, accelerometer_range=RANGE_4G, gyro_range=RANGE_250)

    if mpu6050.is_device_accessible():
        mpu6050.initialize_device()
        mpu6050.start()

        print(f"Accelerometer range: {mpu6050.accelerometer_range}")
        print(f"Gyro range: {mpu6050.gyro_range}")

        for _ in range(50):
            acc = round_readings(mpu6050.get_acceleration())
            gyro = round_readings(mpu6050.get_gyro())
            temp = round(mpu6050.get_temperature(), 2)

            print(f"Temp: {temp}")
            print(f"Acc -> X:{acc[0]} | Y:{acc[1]} | Z:{acc[2]}")
            print(f"Gyro -> X:{gyro[0]} | Y:{gyro[1]} | Z:{gyro[2]}")

            time.sleep(0.5)

        mpu6050.stop()


if __name__ == '__main__':
    main()
