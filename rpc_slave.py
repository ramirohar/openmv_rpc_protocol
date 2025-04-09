import omv
import rpc
import sensor
import struct
import time

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(True)
omv.disable_fb(True)

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

def jpeg_image_snapshot():
    img = sensor.snapshot()
    #img.to_jpeg(quality=90)
    return img

def draw_string(img,x,y,string):
    img.draw_string(x,y,string)

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

def rpc_jpeg_image_snapshot(data):
    try:
        img = jpeg_image_snapshot()
        return RPC_OK + struct.pack("<II", img.height(), img.width())

    except:
        return RPC_FAILED_SNAPSHOT

def rpc_read_fb_chunk(data):

    try:
        offset, chunk_size = struct.unpack("<II", data)
    except:
        return RPC_WRONG_ARGUMENTS

    try:
        fb = sensor.get_fb()
    except:
        return RPC_EMPTY_IMAGE

    if fb is None :
        return RPC_EMPTY_IMAGE

    try:
        bytearr = fb.bytearray()

        if offset + chunk_size > fb.size():
            chunk = bytearr[offset :]
        else:
            chunk = bytearr[offset : offset + chunk_size]
    except:
        return RPC_ERROR

    return RPC_OK + chunk

    #return memoryview(sensor.get_fb().bytearray())[offset : offset + size]

if True:
    interface = rpc.rpc_usb_vcp_slave()
    interface.register_callback(rpc_set_pixelformat)
    interface.register_callback(rpc_set_framesize)
    interface.register_callback(rpc_set_exposure)
    interface.register_callback(rpc_jpeg_image_snapshot)
    interface.register_callback(rpc_read_fb_chunk)
    interface.loop()

else:

    clock = time.clock()

    while True:
        clock.tick()  # Update the FPS clock.

        img_size =  jpeg_image_snapshot()

        print(img_size)
        print(clock.fps())  # Note: OpenMV Cam runs about half as fast when connected

