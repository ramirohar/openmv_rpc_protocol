import struct
import time

import numpy as np

from . import rpc

RPC_OK = struct.pack("<I", 0)
RPC_ERROR = struct.pack("<I", 1)
RPC_WRONG_ARGUMENTS = struct.pack("<I", 2)
RPC_EMPTY_IMAGE = struct.pack("<I", 3)
RPC_FAILED_SNAPSHOT = struct.pack("<I", 4)

# ground_truth = ""


def bytearray_to_img(arr, height, width):
    img_arr = np.frombuffer(arr, dtype=np.uint8)

    if len(img_arr) != height * width:
        raise Exception(
            f"Array length of {len(img_arr)} doesn't match size of {height} x {width}"
        )
    else:
        img_arr = img_arr.reshape((height, width))

        print(img_arr.shape)

        return img_arr


####


def check_status(result):
    if result is None:
        raise Exception("Return message is empty")
    (status,) = struct.unpack("<I", result[:4])

    if status != 0:
        raise Exception(f"RPC Error: {status}")

    return result[4:]


def call_and_check(interface, *args, **kwargs):
    result = interface.call(*args, **kwargs)

    return check_status(result)


#####################


def image_snapshot(interface):
    result = call_and_check(interface, "rpc_image_snapshot")

    height, width = struct.unpack("<II", result)
    size = height * width
    return size, height, width


def image_find_blobs(interface):
    call_and_check(interface, "rpc_image_find_blobs")


def set_exposure(interface, time_ms):
    call_and_check(interface, "rpc_set_exposure", struct.pack("<I", time_ms))

    time.sleep(2)


def set_framesize(interface, framesize):
    call_and_check(interface, "rpc_set_framesize", framesize.encode())


def set_pixelformat(interface, pixelformat):
    call_and_check(interface, "rpc_set_pixelformat", pixelformat.encode())


def read_fb_chunk(interface, offset, max_chunk_size, out, *, retries=5):
    rpc_args = struct.pack("<II", offset, max_chunk_size)

    for _ in range(retries):
        try:
            result = call_and_check(interface, "rpc_read_fb_chunk", rpc_args)

            chunk_size = len(result)

            assert chunk_size <= max_chunk_size
            assert offset + chunk_size <= len(out)

            out[offset : offset + chunk_size] = result  # Write the image data.
            return True
        except Exception as ex:
            print(ex)

    print(f"Failed after {retries} retries")
    return False


###########


class Camara:
    def __init__(
        self,
        port,
        pixformat_str="sensor.GRAYSCALE",
        framesize_str="sensor.QVGA",
        chunksize=1 << 15,
    ):
        self.interface1 = rpc.rpc_usb_vcp_master(port=port)

        self.chunksize = chunksize

        self.set_framsize(framesize_str)

        self.set_pixelformat(pixformat_str)

        time.sleep(2)

    def get_frame_buffer_call_back(self, size):
        img = bytearray(size)
        ok = True
        for offset in range(0, len(img), self.chunksize):
            print(f"Reading {self.chunksize + offset} bytes of {size}")
            ok = ok and read_fb_chunk(self.interface1, offset, self.chunksize, img)
        return ok, img

    def get_snapshot(self):
        size, *specs = image_snapshot(self.interface1)
        ok, img = self.get_frame_buffer_call_back(size)
        return ok, bytearray_to_img(img, *specs)

    def find_blobs(self):
        size, *specs = image_snapshot(self.interface1)
        image_find_blobs(self.interface1)
        ok, img = self.get_frame_buffer_call_back(size)
        return ok, bytearray_to_img(img, *specs)

    def set_framsize(self, framesize_str):
        set_framesize(self.interface1, framesize_str)

    def set_pixelformat(self, pixelformat_str):
        set_pixelformat(self.interface1, pixelformat_str)

    def set_exposure(self, time_ms):
        set_exposure(self.interface1, time_ms)

    def set_chunksize(self, size):
        self.chunksize = size
