import struct
import time

import omv
import pyb
import sensor

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(True)

RPC_OK = struct.pack("<I", 0)
RPC_ERROR = struct.pack("<I", 1)
RPC_WRONG_ARGUMENTS = struct.pack("<I", 2)
RPC_EMPTY_IMAGE = struct.pack("<I", 3)
RPC_FAILED_SNAPSHOT = struct.pack("<I", 4)


def set_exposure(time_ms):
    sensor.set_auto_exposure(False, exposure_us=int(time_ms * 1000))


def set_pixelformat(pixel_format):
    sensor.set_pixformat(pixel_format)


def set_framesize(frame_size):
    sensor.set_framesize(frame_size)


def image_snapshot():
    img = sensor.snapshot()
    # img.to_jpeg(quality=90)
    return img


def draw_string(img, x, y, string):
    img.draw_string(x, y, string)


def image_find_blobs(img):
    stats = img.get_statistics()
    mean, std = stats[0], stats[3]

    blobs = img.find_blobs([(mean - 4 * std, mean + 4 * std)], invert=True)
    for blob in blobs:
        img.draw_rectangle(blob.rect(), color=0)
        img.draw_cross(blob.cx(), blob.cy(), color=0)

    return len(blobs) != 0


######

# def rpc_draw_string(pos, string):
#     try:
#         x,y = struct.unpack("<I", pos)
#         text = bytes(string).decode()
#         return RPC_OK
#     except:


def rpc_set_exposure(data):
    time_ms = struct.unpack("<I", data)[0]
    try:
        set_exposure(time_ms)
        return RPC_OK
    except:
        return RPC_ERROR


def rpc_set_pixelformat(data):
    try:
        pixel_format = eval(bytes(data).decode())
    except:
        return RPC_WRONG_ARGUMENTS

    try:
        set_pixelformat(pixel_format)
        return RPC_OK
    except:
        return RPC_ERROR


def rpc_set_framesize(data):
    try:
        framesize = eval(bytes(data).decode())
    except:
        return RPC_WRONG_ARGUMENTS

    try:
        set_framesize(framesize)
        return RPC_OK
    except:
        return RPC_ERROR


###


def rpc_image_snapshot(data):
    try:
        img = image_snapshot()
        return RPC_OK + struct.pack("<II", img.height(), img.width())

    except:
        return RPC_FAILED_SNAPSHOT


def rpc_image_find_blobs(data):
    try:
        img = sensor.get_fb()
        image_find_blobs(img)
        return RPC_OK
    except:
        return RPC_ERROR


def rpc_read_fb_chunk(data):
    try:
        offset, chunk_size = struct.unpack("<II", data)
    except:
        return RPC_WRONG_ARGUMENTS

    try:
        # fb = TRANSFER_BUFFER
        fb = sensor.get_fb()
    except:
        return RPC_EMPTY_IMAGE

    if fb is None:
        return RPC_EMPTY_IMAGE

    try:
        buf = fb.bytearray()
        # buf = TRANSFER_BUFFER

        if offset + chunk_size > len(buf):
            chunk = buf[offset:]
        else:
            chunk = buf[offset : offset + chunk_size]
    except:
        return RPC_ERROR

    return RPC_OK + chunk

    # return memoryview(sensor.get_fb().bytearray())[offset : offset + size]


def blink():
    for i in [1, 2, 3]:
        pyb.LED(i).on()
        time.sleep(0.5)
        pyb.LED(i).off()


if False:
    import rpc

    omv.disable_fb(True)

    interface = rpc.rpc_usb_vcp_slave()

    blink()

    interface.register_callback(rpc_set_pixelformat)
    interface.register_callback(rpc_set_framesize)
    interface.register_callback(rpc_set_exposure)
    interface.register_callback(rpc_image_snapshot)
    interface.register_callback(rpc_image_find_blobs)
    interface.register_callback(rpc_read_fb_chunk)
    interface.loop()

else:
    from pyb import Pin

    pin = Pin("P1", Pin.OUT_PP, Pin.PULL_NONE)
    while True:
        img = sensor.snapshot()
        print(image_find_blobs(img))
